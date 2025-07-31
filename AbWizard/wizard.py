import sys
import itertools
import csv
from datetime import datetime
from collections import defaultdict
import os

# --- Data Definitions (remain the same) ---
ANTIBODY_PANEL = {
    'Marker1': [{'name': 'CD3-FITC', 'ex': 485, 'em': 520}],
    'Marker2': [{'name': 'CD4-BV510', 'ex': 405, 'em': 520}],
    'Marker3': [{'name': 'CD8-SomeDye', 'ex': 488, 'em': 530}],
    'Marker4': [{'name': 'CD19-APC', 'ex': 638, 'em': 660}],
    'Marker5': [
        {'name': 'CD45-PerCP', 'ex': 488, 'em': 662},
        {'name': 'CD45-BadDye', 'ex': 488, 'em': 658},
    ]
}
INSTRUMENT_CONFIG = {
    'lasers': [405, 488, 638],
    'filters': {
        '450/45': {'center': 450, 'width': 45, 'count': 1},
        '525/40': {'center': 525, 'width': 40, 'count': 2},
        '585/42': {'center': 585, 'width': 42, 'count': 1},
        '610/20': {'center': 610, 'width': 20, 'count': 2},
        '660/10': {'center': 660, 'width': 10, 'count': 2},
        '690/50': {'center': 690, 'width': 50, 'count': 1},
        '712/25': {'center': 712, 'width': 25, 'count': 1},
        '780/60': {'center': 780, 'width': 60, 'count': 3},
    }
}

class Wizard:
    def __init__(self, antibody_panel, instrument_config):
        self.antibody_panel = antibody_panel
        self.instrument_config = instrument_config

    def get_channel_type_for_emission(self, emission_val, filters):
        for name, f in filters.items():
            if f['center'] - f['width'] / 2 <= emission_val < f['center'] + f['width'] / 2:
                return name
        return None

    ### REFINED: The laser matching and filtering logic is now more robust and clearer.
    def prepare_and_filter_panel(self):
        filtered_panel = {}
        print("--- Pre-processing and Filtering Antibodies ---")
        for marker, antibodies in self.antibody_panel.items():
            valid_abs = []
            for ab in antibodies:
                # Find a compatible laser within a +/- 10nm tolerance
                compatible_laser = None
                for laser in self.instrument_config['lasers']:
                    if abs(ab['ex'] - laser) <= 10:
                        compatible_laser = laser
                        break # Found a laser, no need to check others
                
                if not compatible_laser:
                    print(f"  > FILTERED OUT: {ab['name']} (Ex={ab['ex']}nm has no compatible laser)")
                    continue
                
                # Check for a compatible emission channel
                channel_type = self.get_channel_type_for_emission(ab['em'], self.instrument_config['filters'])
                if channel_type is None:
                    print(f"  > FILTERED OUT: {ab['name']} (Em={ab['em']}nm not detected by any filter)")
                    continue
                
                valid_ab = ab.copy()
                valid_ab['channel_type'] = channel_type

                valid_ab['used_laser'] = compatible_laser 
                valid_abs.append(valid_ab)
            
            if valid_abs:
                filtered_panel[marker] = valid_abs
        print("--- Pre-processing Complete ---\n")
        return filtered_panel

    def find_solutions_recursive(self, markers, panel, solution, used_channels, used_slots, all_solutions):
        if not markers:
            all_solutions.append(list(solution))
            return

        marker, remaining_markers = markers[0], markers[1:]

        if marker not in panel:
            self.find_solutions_recursive(remaining_markers, panel, solution, used_channels, used_slots, all_solutions)
            return

        for ab in panel[marker]:
            channel_type = ab['channel_type']

            instrument_slot = (ab['used_laser'], channel_type)

            is_slot_free = instrument_slot not in used_slots

            is_channel_available = used_channels[channel_type] < self.instrument_config['filters'][channel_type]['count']
            
            if is_slot_free and is_channel_available:
                solution.append({'marker': marker, **ab})
                used_channels[channel_type] += 1
                used_slots.add(instrument_slot)
                
                self.find_solutions_recursive(remaining_markers, panel, solution, used_channels, used_slots, all_solutions)

                used_slots.remove(instrument_slot)
                used_channels[channel_type] -= 1
                solution.pop()

    def save_results_to_csv(self, results, filename):
        if not results:
            print("No results to save.")
            return
        headers = ['Solution_Set_ID','Panel_ID','Markers_Used','Markers_Omitted','Marker','Antibody_Name','Excitation_Laser (nm)','Emission_Wavelength (nm)','Detector_Channel']
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for set_id, result_package in enumerate(results, 1):
                mu_str = ', '.join(result_package['markers_used'])
                mo_str = ', '.join(result_package['markers_omitted'])
                for panel_id, panel in enumerate(result_package['solutions'], 1):
                    for antibody in panel:
                        writer.writerow({
                            'Solution_Set_ID': set_id, 'Panel_ID': panel_id,
                            'Markers_Used': mu_str, 'Markers_Omitted': mo_str,
                            'Marker': antibody['marker'], 'Antibody_Name': antibody['name'],
                            ### REFINED: Report the actual laser used in the CSV.
                            'Excitation_Laser (nm)': antibody['used_laser'],
                            'Emission_Wavelength (nm)': antibody['em'],
                            'Detector_Channel': antibody['channel_type']
                        })
        print(f"\nResults successfully saved to {filename}")


    def find_best_solution(self, compatible_panel):

        all_marker_names = list(compatible_panel.keys())
        
        for num_markers in range(len(all_marker_names), 0, -1):
            print(f"--- Searching for solutions with {num_markers} markers ---")
            
            marker_combinations = itertools.combinations(all_marker_names, num_markers)
            found_solutions = []
            
            for marker_combo in marker_combinations:
                solutions_for_this_combo = []
                self.find_solutions_recursive(
                    list(marker_combo), 
                    compatible_panel, # Use the filtered panel
                    [], defaultdict(int), set(), solutions_for_this_combo
                )
                
                if solutions_for_this_combo:
                    omitted = set(self.antibody_panel.keys()) - set(marker_combo)
                    found_solutions.append({
                        "markers_used": list(marker_combo),
                        "markers_omitted": list(omitted),
                        "solutions": solutions_for_this_combo
                    })

            if found_solutions:
                print(f"\nSUCCESS: Found solution set(s) for {num_markers} markers.")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop') 
                filename = f"antibody_panels_{timestamp}.csv"
                self.save_results_to_csv(found_solutions, os.path.join(desktop, filename))
                return found_solutions

        print("No possible solution found.")
        return None


    def run(self):
        """Runs the entire analysis process."""
        compatible_panel = self.prepare_and_filter_panel()
        if compatible_panel:
            self.find_best_solution(compatible_panel)
        else:
            print("No antibodies were compatible with the instrument.")

if __name__ == "__main__":
    wizard = Wizard(ANTIBODY_PANEL, INSTRUMENT_CONFIG)

    wizard.run()