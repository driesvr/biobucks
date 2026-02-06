#!/usr/bin/env python3
"""
Simple HTTP server for BioBucks DCF Valuations viewer.
Uses only Python standard library - no external dependencies.

Usage:
    python3 server.py [port]

Default port: 8000
"""

import http.server
import socketserver
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse
from datetime import datetime
import math

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
VALUATIONS_DIR = Path(__file__).parent / "valuations"


def parse_value(value_str):
    """Parse a numeric value from a string, removing commas and non-numeric characters."""
    if isinstance(value_str, (int, float)):
        return float(value_str)
    return float(str(value_str).replace(',', '').replace('$', '').strip())


def get_param_value(param, default=0):
    """Safely extract numeric value from a parameter object."""
    if not param or 'value' not in param:
        return default
    try:
        return parse_value(param['value'])
    except (ValueError, TypeError):
        return default


def calculate_phase_fractions(year, phase_i_duration, phase_i_end, phase_ii_duration, phase_ii_end,
                              phase_iii_duration, phase_iii_end, approval_duration, approval_end):
    """Calculate the overlap fraction of each clinical phase within a given year.

    Returns a list of (phase_name, phase_key, fraction) tuples for phases
    that overlap with [year, year+1).
    """
    year_start = float(year)
    year_end = float(year + 1)
    fractions = []

    # Phase I overlap
    if phase_i_duration > 0 and year_start < phase_i_end:
        overlap = min(year_end, phase_i_end) - max(year_start, 0)
        if overlap > 0:
            fractions.append(('Phase I', 'phaseI', overlap))

    # Phase II overlap
    if phase_ii_duration > 0 and year_start < phase_ii_end and year_end > phase_i_end:
        overlap = min(year_end, phase_ii_end) - max(year_start, phase_i_end)
        if overlap > 0:
            fractions.append(('Phase II', 'phaseII', overlap))

    # Phase III overlap
    if phase_iii_duration > 0 and year_start < phase_iii_end and year_end > phase_ii_end:
        overlap = min(year_end, phase_iii_end) - max(year_start, phase_ii_end)
        if overlap > 0:
            fractions.append(('Phase III', 'phaseIII', overlap))

    # Approval overlap
    if approval_duration > 0 and year_start < approval_end and year_end > phase_iii_end:
        overlap = min(year_end, approval_end) - max(year_start, phase_iii_end)
        if overlap > 0:
            fractions.append(('Approval Process', 'approval', overlap))

    return fractions


def calculate_dcf(valuation_data):
    """Calculate DCF projections for a biotech asset."""
    params = valuation_data

    # Parse market parameters
    tam = get_param_value(params.get('marketParameters', {}).get('totalAddressableMarket', {}))
    peak_share = get_param_value(params.get('marketParameters', {}).get('peakMarketShare', {})) / 100
    years_to_peak = get_param_value(params.get('marketParameters', {}).get('yearsToPeakAdoption', {}))
    pricing = get_param_value(params.get('marketParameters', {}).get('annualPricing', {}))
    loe = get_param_value(params.get('marketParameters', {}).get('lossOfExclusivity', {}))
    years_to_decline = get_param_value(params.get('marketParameters', {}).get('yearsToDeclinePostLOE', {}))
    terminal_share = get_param_value(params.get('marketParameters', {}).get('terminalMarketShare', {})) / 100

    # Get current development stage
    current_stage = params.get('assetOverview', {}).get('currentDevelopmentStage') or params.get('assetOverview', {}).get('currentDevelopmentPhase', 'Phase I Ready')
    current_stage_lower = current_stage.lower()

    # Map current stage to numeric value
    stage_map = {
        'preclinical ready': 0, 'preclinical': 0, 'discovery': 0,
        'phase i ready': 1, 'phase i': 1, 'phase 1 ready': 1, 'phase 1': 1,
        'phase ii ready': 2, 'phase ii': 2, 'phase 2 ready': 2, 'phase 2': 2,
        'phase iii ready': 3, 'phase iii': 3, 'phase 3 ready': 3, 'phase 3': 3,
        'registration ready': 4, 'approval': 4,
        'approved': 5
    }
    current_stage_value = stage_map.get(current_stage_lower) 

    # Parse development timeline - get individual phase durations
    dev_timeline = params.get('developmentTimeline', {})

    # Get durations for current and future phases only
    phase_i_duration = get_param_value(dev_timeline.get('phaseIDuration', {}), 0) if current_stage_value <= 1 else 0
    phase_ii_duration = get_param_value(dev_timeline.get('phaseIIDuration', {}), 0) if current_stage_value <= 2 else 0
    phase_iii_duration = get_param_value(dev_timeline.get('phaseIIIDuration', {}), 0) if current_stage_value <= 3 else 0
    approval_duration = get_param_value(dev_timeline.get('approvalDuration', {}), 0) if current_stage_value <= 4 else 0

    # Calculate cumulative phase end times
    years_to_approval = phase_i_duration + phase_ii_duration + phase_iii_duration + approval_duration
    phase_i_end = phase_i_duration
    phase_ii_end = phase_i_end + phase_ii_duration
    phase_iii_end = phase_ii_end + phase_iii_duration
    approval_end = phase_iii_end + approval_duration

    # Parse clinical trial costs (in millions) - only for current and future phases
    costs = {
        'phaseI': get_param_value(params.get('clinicalTrialCosts', {}).get('phaseI', {}), 0) * 1_000_000 if current_stage_value <= 1 else 0,
        'phaseII': get_param_value(params.get('clinicalTrialCosts', {}).get('phaseII', {}), 0) * 1_000_000 if current_stage_value <= 2 else 0,
        'phaseIII': get_param_value(params.get('clinicalTrialCosts', {}).get('phaseIII', {}), 0) * 1_000_000 if current_stage_value <= 3 else 0,
        'approval': get_param_value(params.get('clinicalTrialCosts', {}).get('approval', {}), 0) * 1_000_000 if current_stage_value <= 4 else 0
    }

    # Calculate annual costs for each phase (distribute over phase duration)
    annual_costs = {
        'phaseI': costs['phaseI'] / phase_i_duration if phase_i_duration > 0 else 0,
        'phaseII': costs['phaseII'] / phase_ii_duration if phase_ii_duration > 0 else 0,
        'phaseIII': costs['phaseIII'] / phase_iii_duration if phase_iii_duration > 0 else 0,
        'approval': costs['approval'] / approval_duration if approval_duration > 0 else 0
    }

    # Parse probability of success - only for current and future phases
    # Cap each phase at 100% to prevent invalid inputs
    pos = {
        'phaseI': min(get_param_value(params.get('probabilityOfSuccess', {}).get('phaseI', {}), 100) / 100, 1.0) if current_stage_value <= 1 else 1.0,
        'phaseII': min(get_param_value(params.get('probabilityOfSuccess', {}).get('phaseII', {}), 100) / 100, 1.0) if current_stage_value <= 2 else 1.0,
        'phaseIII': min(get_param_value(params.get('probabilityOfSuccess', {}).get('phaseIII', {}), 100) / 100, 1.0) if current_stage_value <= 3 else 1.0,
        'approval': min(get_param_value(params.get('probabilityOfSuccess', {}).get('approval', {}), 100) / 100, 1.0) if current_stage_value <= 4 else 1.0
    }
    cumulative_pos = pos['phaseI'] * pos['phaseII'] * pos['phaseIII'] * pos['approval']

    # Parse financial parameters
    cogs = get_param_value(params.get('financialParameters', {}).get('costOfGoodsSold', {}), 0) / 100
    opex = get_param_value(params.get('financialParameters', {}).get('operatingExpenses', {}), 0) / 100
    tax_rate = get_param_value(params.get('financialParameters', {}).get('taxRate', {}), 0) / 100
    wacc = get_param_value(params.get('financialParameters', {}).get('discountRate', {}), 10) / 100

    # Build year-by-year projections
    projection_years = math.ceil(years_to_approval + loe + years_to_decline)
    years = []

    for year in range(projection_years + 1):
        year_data = {
            'year': year,
            'label': 'Current year' if year == 0 else f'Year {year}'
        }

        # Determine stage and costs for this year
        if year < years_to_approval:
            # Development phases - calculate partial year cost allocation
            phase_fractions = calculate_phase_fractions(
                year, phase_i_duration, phase_i_end, phase_ii_duration, phase_ii_end,
                phase_iii_duration, phase_iii_end, approval_duration, approval_end
            )

            total_dev_cost = sum(annual_costs[key] * frac for _, key, frac in phase_fractions)

            # Determine primary stage (phase with largest fraction)
            if phase_fractions:
                year_data['stage'] = max(phase_fractions, key=lambda x: x[2])[0]
            else:
                year_data['stage'] = current_stage

            year_data['developmentCosts'] = total_dev_cost
            year_data['revenue'] = 0
            year_data['cogs'] = 0
            year_data['opex'] = 0
            year_data['ebit'] = -year_data['developmentCosts']
            year_data['tax'] = 0
            year_data['fcf'] = -year_data['developmentCosts']
        else:
            # Commercial phase
            years_from_approval = year - years_to_approval

            # Combine launch with first year of market ramp
            if years_from_approval < years_to_peak:
                year_data['stage'] = 'Market Ramp'
            elif years_from_approval < loe:
                year_data['stage'] = 'Peak Sales'
            elif years_from_approval < loe + years_to_decline:
                year_data['stage'] = 'Post-LOE Decline'
            else:
                year_data['stage'] = 'Generic Competition'

            # Market share calculation - start ramping from year 0 (launch year)
            if years_from_approval < years_to_peak:
                # Linear ramp from year 0 to peak
                market_share = peak_share * ((years_from_approval + 1) / years_to_peak) if years_to_peak > 0 else peak_share
            elif years_from_approval <= loe:
                market_share = peak_share
            elif years_from_approval <= loe + years_to_decline:
                years_into_decline = years_from_approval - loe
                decline_progress = years_into_decline / years_to_decline if years_to_decline > 0 else 1
                market_share = peak_share * (1 - (1 - terminal_share) * decline_progress)
            else:
                market_share = peak_share * terminal_share

            year_data['developmentCosts'] = 0
            year_data['revenue'] = tam * market_share * pricing
            year_data['cogs'] = year_data['revenue'] * cogs
            year_data['opex'] = year_data['revenue'] * opex
            year_data['ebit'] = year_data['revenue'] - year_data['cogs'] - year_data['opex']
            year_data['tax'] = year_data['ebit'] * tax_rate if year_data['ebit'] > 0 else 0
            year_data['fcf'] = year_data['ebit'] - year_data['tax']

        # Phase-specific risk adjustment
        # Each phase's costs are only incurred if prior phases succeed
        # Commercial revenues require all phases to succeed
        if year < years_to_approval:
            # Apply cumulative prior-phase success probability to each phase's costs
            prior_risk = {
                'phaseI': 1.0,
                'phaseII': pos['phaseI'],
                'phaseIII': pos['phaseI'] * pos['phaseII'],
                'approval': pos['phaseI'] * pos['phaseII'] * pos['phaseIII']
            }

            risk_adjusted_cost = sum(
                annual_costs[key] * frac * prior_risk[key]
                for _, key, frac in phase_fractions
            )

            year_data['riskAdjustedFCF'] = -risk_adjusted_cost

            # Set risk phase description based on primary phase
            if year < phase_i_end:
                year_data['riskPhase'] = 'Phase I (no prior risk)'
            elif year < phase_ii_end:
                year_data['riskPhase'] = 'Phase II (Phase I PoS applied)'
            elif year < phase_iii_end:
                year_data['riskPhase'] = 'Phase III (Phase I × II PoS applied)'
            elif year < approval_end:
                year_data['riskPhase'] = 'Approval (Phase I × II × III PoS applied)'
            else:
                year_data['riskPhase'] = 'Development (full PoS)'
        else:
            # Commercial phase - revenues only occur if all phases succeed
            year_data['riskAdjustedFCF'] = year_data['fcf'] * cumulative_pos
            year_data['riskPhase'] = 'Commercial (full cumulative PoS)'

        # Discount to present value
        year_data['discountFactor'] = (1 + wacc) ** (-year)
        year_data['presentValue'] = year_data['riskAdjustedFCF'] * year_data['discountFactor']

        years.append(year_data)

    # Calculate NPV
    npv = sum(y['presentValue'] for y in years)

    return {
        'years': years,
        'npv': npv,
        'cumulativePoS': cumulative_pos,
        'wacc': wacc,
        'yearsToApproval': years_to_approval
    }


class BioBucksHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for BioBucks API endpoints and static files."""

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)

        # API endpoint: List all valuations
        if parsed_path.path == "/api/valuations":
            self.handle_list_valuations()

        # API endpoint: Get specific valuation
        elif parsed_path.path.startswith("/api/valuations/") and "/dcf" in parsed_path.path:
            valuation_id = parsed_path.path.split("/")[-2]
            self.handle_calculate_dcf(valuation_id)

        # API endpoint: Get specific valuation
        elif parsed_path.path.startswith("/api/valuations/"):
            valuation_id = parsed_path.path.split("/")[-1]
            self.handle_get_valuation(valuation_id)

        # Serve static HTML file
        elif parsed_path.path == "/" or parsed_path.path == "/index.html":
            self.serve_index()

        # Ignore favicon.ico requests silently
        elif parsed_path.path == "/favicon.ico":
            self.send_response(404)
            self.end_headers()

        # Default behavior for other files
        else:
            super().do_GET()

    def do_PUT(self):
        """Handle PUT requests."""
        parsed_path = urlparse(self.path)

        # API endpoint: Update valuation
        if parsed_path.path.startswith("/api/valuations/"):
            valuation_id = parsed_path.path.split("/")[-1]
            self.handle_update_valuation(valuation_id)
        else:
            self.send_error_response(404, "Not found")

    def do_DELETE(self):
        """Handle DELETE requests."""
        parsed_path = urlparse(self.path)

        # API endpoint: Delete valuation
        if parsed_path.path.startswith("/api/valuations/"):
            valuation_id = parsed_path.path.split("/")[-1]
            self.handle_delete_valuation(valuation_id)
        else:
            self.send_error_response(404, "Not found")

    def handle_list_valuations(self):
        """Return list of all valuation JSON files."""
        try:
            # Ensure valuations directory exists
            VALUATIONS_DIR.mkdir(exist_ok=True)

            valuations = []
            for json_file in VALUATIONS_DIR.glob("*.json"):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        valuations.append({
                            "id": json_file.stem,  # filename without extension
                            "filename": json_file.name,
                            "assetName": data.get("assetOverview", {}).get("assetName", "Unknown Asset"),
                            "therapeuticArea": data.get("assetOverview", {}).get("therapeuticArea", ""),
                            "generatedDate": data.get("metadata", {}).get("generatedDate", "")
                        })
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error reading {json_file}: {e}")
                    continue

            # Sort by generated date (newest first)
            valuations.sort(key=lambda x: x.get("generatedDate", ""), reverse=True)

            self.send_json_response(valuations)

        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_get_valuation(self, valuation_id):
        """Return specific valuation JSON file."""
        try:
            json_file = VALUATIONS_DIR / f"{valuation_id}.json"

            if not json_file.exists():
                self.send_error_response(404, "Valuation not found")
                return

            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.send_json_response(data)

        except json.JSONDecodeError as e:
            self.send_error_response(400, f"Invalid JSON: {e}")
        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_calculate_dcf(self, valuation_id):
        """Calculate and return DCF for a specific valuation."""
        try:
            json_file = VALUATIONS_DIR / f"{valuation_id}.json"

            if not json_file.exists():
                self.send_error_response(404, "Valuation not found")
                return

            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            dcf_results = calculate_dcf(data)
            self.send_json_response(dcf_results)

        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_update_valuation(self, valuation_id):
        """Update a valuation with new parameters."""
        try:
            json_file = VALUATIONS_DIR / f"{valuation_id}.json"

            if not json_file.exists():
                self.send_error_response(404, "Valuation not found")
                return

            # Get update from request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            update_data = json.loads(body.decode('utf-8'))

            # Save updated data directly (frontend sends complete valuation object)
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(update_data, f, indent=2)

            self.send_json_response(update_data)

        except json.JSONDecodeError as e:
            self.send_error_response(400, f"Invalid JSON: {e}")
        except Exception as e:
            self.send_error_response(500, str(e))

    def handle_delete_valuation(self, valuation_id):
        """Delete a valuation file."""
        try:
            json_file = VALUATIONS_DIR / f"{valuation_id}.json"

            if not json_file.exists():
                self.send_error_response(404, "Valuation not found")
                return

            # Delete the file
            json_file.unlink()

            self.send_json_response({"success": True, "message": "Valuation deleted successfully"})

        except Exception as e:
            self.send_error_response(500, str(e))

    def serve_index(self):
        """Serve the main HTML page."""
        html_file = Path(__file__).parent / "index.html"

        if not html_file.exists():
            self.send_error_response(404, "index.html not found. Please create it first.")
            return

        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content.encode('utf-8'))))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))

        except Exception as e:
            self.send_error_response(500, str(e))

    def send_json_response(self, data):
        """Send JSON response."""
        json_data = json.dumps(data, indent=2)

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(json_data.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))

    def send_error_response(self, code, message):
        """Send error response."""
        error_data = {"error": message}
        json_data = json.dumps(error_data)

        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", str(len(json_data.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(json_data.encode('utf-8'))

    def log_message(self, format, *args):
        """Custom log format."""
        sys.stdout.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}\n")

    def handle(self):
        """Override handle to catch BrokenPipeError."""
        try:
            super().handle()
        except BrokenPipeError:
            # Client closed connection before we could send response
            # This is common for favicon requests - just ignore it
            pass


def main():
    """Start the server."""
    # Ensure valuations directory exists
    VALUATIONS_DIR.mkdir(exist_ok=True)

    # Enable SO_REUSEADDR to allow immediate rebinding
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer(("", PORT), BioBucksHandler) as httpd:
        print(f"\n{'='*60}")
        print(f"  BioBucks DCF Valuations Viewer")
        print(f"{'='*60}")
        print(f"\n  Server running at: http://localhost:{PORT}")
        print(f"  Valuations directory: {VALUATIONS_DIR}")
        print(f"\n  Press Ctrl+C to stop the server\n")
        print(f"{'='*60}\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down server...")
            httpd.shutdown()


if __name__ == "__main__":
    main()
