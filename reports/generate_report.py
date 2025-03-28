import os

def generate_report():
    logs = [
        'detection/behavioral_analysis.log',
        'detection/file_system_monitoring.log',
        'detection/network_traffic_analysis.log',
        'detection/registry_monitoring.log',
        'detection/process_monitoring.log',
        'detection/static_analysis.log',
        'prevention/moving_target_defense.log'
    ]

    summary_file_path = 'reports/summary_report.txt'
    detailed_report_file_path = 'reports/detection_and_prevention_report.txt'

    # Generate Detailed Report
    with open(detailed_report_file_path, 'w') as report_file:
        for log_file in logs:
            if os.path.exists(log_file):
                with open(log_file, 'r') as file:
                    report_file.write(f"--- {log_file} ---\n")
                    report_file.write(file.read())
                    report_file.write("\n\n")
    
    # Generate Summary Report
    with open(summary_file_path, 'w') as summary_file:
        summary_file.write("Summary Report\n")
        summary_file.write("="*50 + "\n")

        # Check for suspicious activities
        suspicious_detected = False
        prevention_done = False

        for log_file in logs:
            if os.path.exists(log_file):
                with open(log_file, 'r') as file:
                    content = file.read()
                    if 'suspicious' in content.lower():
                        suspicious_detected = True
                    if 'prevention' in content.lower():
                        prevention_done = True

        if suspicious_detected:
            summary_file.write("Suspicious Activity Detected!\n")
        else:
            summary_file.write("No Suspicious Activity Detected.\n")

        if prevention_done:
            summary_file.write("Prevention Actions Taken.\n")
        else:
            summary_file.write("No Prevention Actions Taken.\n")

        # Optionally add more specific summaries based on log content
        # Example:
        summary_file.write("\nDetailed Findings:\n")
        for log_file in logs:
            if os.path.exists(log_file):
                with open(log_file, 'r') as file:
                    content = file.read()
                    if 'suspicious' in content.lower() or 'prevention' in content.lower():
                        summary_file.write(f"--- {log_file} ---\n")
                        summary_file.write(content)
                        summary_file.write("\n\n")

    return summary_file_path

if __name__ == "__main__":
    summary_path = generate_report()
    print(f"Summary report generated at: {summary_path}")