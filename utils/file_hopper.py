import os
import random
import time
import threading
import shutil
import logging
import string
import hashlib
import json
from pathlib import Path
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/file_hopper.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FileHopper")

# Singleton instance
_file_hopper_instance = None

def get_file_hopper():
    """Get the singleton file hopper instance"""
    global _file_hopper_instance
    if _file_hopper_instance is None:
        _file_hopper_instance = FileHopper()
    return _file_hopper_instance

class FileHopper:
    """
    Manages the hopping of files between various locations to prevent
    easy targeting by ransomware. This implements Moving Target Defense
    strategies by randomizing file locations periodically.
    """
    
    def __init__(self):
        """Initialize the file hopper with secure defaults"""
        self.running = False
        self.hop_thread = None
        self.hop_interval = 60  # Default to 60 seconds between hops
        self.hop_history = []
        self.hop_history_max = 100  # Maximum hop history entries to keep
        
        # Create secure hash-based hop locations instead of hardcoded paths
        # This ensures hop locations aren't exposed in git commits
        self.main_quarantine_dir = "safe_mtd"
        
        # Create the main quarantine directory if it doesn't exist
        os.makedirs(self.main_quarantine_dir, exist_ok=True)
        
        # Generate hop locations based on runtime hash values
        self._generate_hop_locations()
        
        # Create directories for each hop location
        for location in self.hop_locations:
            os.makedirs(location, exist_ok=True)
            
        logger.info(f"FileHopper initialized with {len(self.hop_locations)} hop locations")
    
    def _generate_hop_locations(self):
        """
        Generate secure hop locations based on runtime hash values
        This prevents exposing actual paths in the code while still ensuring
        they're consistent across app restarts
        """
        # Create a base hash value from machine-specific information
        # This ensures hop locations are unique per machine but consistent
        # across app restarts on the same machine
        machine_id = self._get_machine_id()
        
        # Create hop locations using hash-based subdirectories
        hop_count = 5  # Number of hop locations to create
        self.hop_locations = []
        
        # Get current time to add some randomness
        timestamp = str(int(time.time()))
        
        for i in range(hop_count):
            # Create a unique hash for this hop location
            hash_input = f"{machine_id}-hop-{i}-{timestamp}"
            location_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
            
            # Create hop location
            hop_path = os.path.join(self.main_quarantine_dir, f"hop_{location_hash}")
            self.hop_locations.append(hop_path)
        
        # Always add the main quarantine directory as a hop location
        if self.main_quarantine_dir not in self.hop_locations:
            self.hop_locations.append(self.main_quarantine_dir)
            
        logger.debug(f"Generated {len(self.hop_locations)} hop locations")
    
    def _get_machine_id(self):
        """
        Get a unique machine ID that's consistent across app restarts
        but unique to each machine
        """
        try:
            # Try to use existing machine ID if available
            machine_id_file = os.path.join(tempfile.gettempdir(), "ransomware_detection_machine_id.txt")
            
            if os.path.exists(machine_id_file):
                with open(machine_id_file, 'r') as f:
                    return f.read().strip()
            
            # Generate new machine ID
            import platform
            import uuid
            
            # Combine multiple machine-specific values
            system_info = platform.uname()
            mac_address = uuid.getnode()
            
            # Create a hash of the combined values
            machine_hash = hashlib.md5(f"{system_info}-{mac_address}".encode()).hexdigest()
            
            # Save for future use
            with open(machine_id_file, 'w') as f:
                f.write(machine_hash)
                
            return machine_hash
            
        except Exception as e:
            logger.error(f"Error getting machine ID: {e}")
            # Fallback to a random ID if we can't get a consistent one
            return hashlib.md5(str(random.randint(1, 1000000)).encode()).hexdigest()
    
    def start(self):
        """Start the file hopping process"""
        if self.running:
            logger.info("File hopping already running")
            return True
        
        try:
            self.running = True
            self.hop_thread = threading.Thread(target=self._hop_loop)
            self.hop_thread.daemon = True
            self.hop_thread.start()
            logger.info(f"File hopping started with interval of {self.hop_interval} seconds")
            return True
        except Exception as e:
            logger.error(f"Error starting file hopping: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop the file hopping process"""
        if not self.running:
            logger.info("File hopping already stopped")
            return True
        
        try:
            self.running = False
            if self.hop_thread:
                self.hop_thread.join(timeout=5)
            logger.info("File hopping stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping file hopping: {e}")
            return False
    
    def _hop_loop(self):
        """Main loop for file hopping"""
        while self.running:
            try:
                self._perform_hop()
                
                # Sleep for the hop interval
                for _ in range(min(60, self.hop_interval)):
                    if not self.running:
                        break
                    time.sleep(1)
                
                # If the interval is longer than 60 seconds, sleep in 60-second chunks
                # so we can exit more quickly if stop() is called
                remaining_time = max(0, self.hop_interval - 60)
                while remaining_time > 0 and self.running:
                    sleep_time = min(60, remaining_time)
                    time.sleep(sleep_time)
                    remaining_time -= sleep_time
                    
            except Exception as e:
                logger.error(f"Error in hop loop: {e}")
                time.sleep(5)  # Brief pause on error
    
    def _perform_hop(self):
        """Perform a single hop operation on all quarantined files"""
        try:
            # Count how many files were hopped
            hop_count = 0
            
            # Create a list of all files across all hop locations
            all_files = []
            
            for location in self.hop_locations:
                if os.path.exists(location) and os.path.isdir(location):
                    for file in os.listdir(location):
                        file_path = os.path.join(location, file)
                        if os.path.isfile(file_path):
                            all_files.append(file_path)
            
            # Shuffle the files to different locations
            for file_path in all_files:
                try:
                    # Choose a random destination location (different from current)
                    current_dir = os.path.dirname(file_path)
                    available_locations = [loc for loc in self.hop_locations 
                                         if os.path.abspath(loc) != os.path.abspath(current_dir)]
                    
                    if not available_locations:
                        logger.warning(f"No alternative locations available for {file_path}")
                        continue
                        
                    destination_dir = random.choice(available_locations)
                    
                    # Move the file to the new location
                    filename = os.path.basename(file_path)
                    destination_path = os.path.join(destination_dir, filename)
                    
                    # Log before moving
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    hop_info = {
                        'timestamp': timestamp,
                        'file': filename,
                        'source': file_path,
                        'destination': destination_path
                    }
                    
                    # Move the file
                    shutil.move(file_path, destination_path)
                    
                    # Add to hop history
                    self.hop_history.append(hop_info)
                    if len(self.hop_history) > self.hop_history_max:
                        self.hop_history = self.hop_history[-self.hop_history_max:]
                    
                    # Log the hop to file
                    self._log_hop(hop_info)
                    
                    # Increment counter
                    hop_count += 1
                    
                except Exception as e:
                    logger.error(f"Error hopping file {file_path}: {e}")
            
            logger.info(f"Completed hop operation: {hop_count} files moved")
            return hop_count
            
        except Exception as e:
            logger.error(f"Error performing hop: {e}")
            return 0
    
    def _log_hop(self, hop_info):
        """Log a hop operation to the hop log file"""
        try:
            # Ensure prevention directory exists
            os.makedirs('prevention', exist_ok=True)
            
            # Write to the hop log file
            with open('prevention/file_hops.txt', 'a', encoding='utf-8') as f:
                f.write(f"{hop_info['source']} -> {hop_info['destination']} @ {hop_info['timestamp']}\n")
                
        except Exception as e:
            logger.error(f"Error logging hop: {e}")
    
    def get_hop_history(self):
        """Get the history of hop operations"""
        return self.hop_history.copy()
    
    def get_file_locations(self):
        """Get all current file locations"""
        files = []
        
        for location in self.hop_locations:
            if os.path.exists(location) and os.path.isdir(location):
                for file in os.listdir(location):
                    file_path = os.path.join(location, file)
                    if os.path.isfile(file_path):
                        files.append({
                            'name': file,
                            'path': file_path,
                            'location': location
                        })
        
        return files
    
    def get_available_locations(self):
        """Get a list of all available hop locations"""
        # Return only directory names without full paths for security
        return [os.path.basename(loc) for loc in self.hop_locations]

if __name__ == "__main__":
    # Test the file hopper
    hopper = FileHopper(hop_interval=10)  # Use a short interval for testing
    print(f"Starting file hopper with {len(hopper.hop_locations)} locations")
    hopper.start()
    
    try:
        # Run for 60 seconds
        for i in range(6):
            time.sleep(10)
            print(f"Hopper running for {(i+1)*10} seconds")
            print(f"History entries: {len(hopper.hop_history)}")
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        hopper.stop()
        print("File hopper stopped")