import os
import json
import logging

class ConfigManager:
    '''Configuration manager for META Simulator'''
    
    def __init__(self, config_file=None):
        '''Initialize with optional config file'''
        self.logger = logging.getLogger("CONFIG_MANAGER")
        self.config_data = {}
        self._logs_dir = "logs"
        self._data_dir = "data"
        self._pgn_dir = "results/pgn"
        self._reports_dir = "results/reports"
        self._stats_dir = "results/stats"
        self._backup_dir = "backups"
        self._use_stockfish = False
        
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
        else:
            self.load_defaults()
        
        # Ensure dirs exist
        os.makedirs(self.LOGS_DIR, exist_ok=True)
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.PGN_DIR, exist_ok=True)
        os.makedirs(self.REPORTS_DIR, exist_ok=True)
        os.makedirs(self.STATS_DIR, exist_ok=True)
        os.makedirs(self.BACKUP_DIR, exist_ok=True)
        
        self.logger.info("ConfigManager initialized")
    
    def load_from_file(self, config_file):
        '''Load configuration from file'''
        try:
            with open(config_file, 'r') as f:
                self.config_data = json.load(f)
            self.logger.info(f"Loaded configuration from {config_file}")
            
            # Update property values from config
            if "paths" in self.config_data:
                paths = self.config_data["paths"]
                if "logs_dir" in paths:
                    self._logs_dir = paths["logs_dir"]
                if "data_dir" in paths:
                    self._data_dir = paths["data_dir"]
                if "pgn_dir" in paths:
                    self._pgn_dir = paths["pgn_dir"]
                if "reports_dir" in paths:
                    self._reports_dir = paths["reports_dir"]
                if "stats_dir" in paths:
                    self._stats_dir = paths["stats_dir"]
                if "backup_dir" in paths:
                    self._backup_dir = paths["backup_dir"]
            
            # Update features
            if "features" in self.config_data:
                features = self.config_data["features"]
                if "use_stockfish" in features:
                    self._use_stockfish = features["use_stockfish"]
        except Exception as e:
            self.logger.warning(f"Failed to load config from {config_file}: {e}")
            self.load_defaults()
    
    def load_defaults(self):
        '''Load default configuration'''
        self.config_data = {
            "simulator": {
                "version": "4.2.1",
                "name": "META Fantasy League Simulator"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "paths": {
                "logs_dir": self._logs_dir,
                "data_dir": self._data_dir,
                "pgn_dir": self._pgn_dir,
                "reports_dir": self._reports_dir,
                "stats_dir": self._stats_dir,
                "backup_dir": self._backup_dir
            },
            "features": {
                "per_board_pgn": True,
                "aggregate_match_pgn": True,
                "stamina_enabled": True,
                "injury_enabled": True,
                "use_stockfish": self._use_stockfish,
                "xp_enabled": False,
                "synergy_enabled": False,
                "morale_enabled": False
            },
            "simulation": {
                "teams_per_match": 8,
                "matches_per_day": 5,
                "ko_threshold": 4,
                "team_hp_threshold": 30,
                "max_moves": 30,
                "home_advantage_factor": 0.1
            }
        }
    
    def get(self, key_path, default=None):
        '''Get configuration value by dot-separated path'''
        parts = key_path.split('.')
        current = self.config_data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return current
    
    def set(self, key_path, value):
        '''Set configuration value by dot-separated path'''
        parts = key_path.split('.')
        current = self.config_data
        
        # Navigate to the innermost dictionary
        for i, part in enumerate(parts[:-1]):
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        
        # Set the value
        current[parts[-1]] = value
    
    @property
    def LOG_DIR(self):
        '''Get logs directory path (alias for LOGS_DIR)'''
        return self._logs_dir
    
    @LOG_DIR.setter
    def LOG_DIR(self, value):
        '''Set logs directory path'''
        self._logs_dir = value
        self.set('paths.logs_dir', value)
    
    @property
    def LOGS_DIR(self):
        '''Get logs directory path'''
        return self._logs_dir
    
    @LOGS_DIR.setter
    def LOGS_DIR(self, value):
        '''Set logs directory path'''
        self._logs_dir = value
        self.set('paths.logs_dir', value)
    
    @property
    def DATA_DIR(self):
        '''Get data directory path'''
        return self._data_dir
    
    @DATA_DIR.setter
    def DATA_DIR(self, value):
        '''Set data directory path'''
        self._data_dir = value
        self.set('paths.data_dir', value)
    
    @property
    def PGN_DIR(self):
        '''Get PGN directory path'''
        return self._pgn_dir
    
    @PGN_DIR.setter
    def PGN_DIR(self, value):
        '''Set PGN directory path'''
        self._pgn_dir = value
        self.set('paths.pgn_dir', value)
    
    @property
    def REPORTS_DIR(self):
        '''Get reports directory path'''
        return self._reports_dir
    
    @REPORTS_DIR.setter
    def REPORTS_DIR(self, value):
        '''Set reports directory path'''
        self._reports_dir = value
        self.set('paths.reports_dir', value)
    
    @property
    def STATS_DIR(self):
        '''Get stats directory path'''
        return self._stats_dir
    
    @STATS_DIR.setter
    def STATS_DIR(self, value):
        '''Set stats directory path'''
        self._stats_dir = value
        self.set('paths.stats_dir', value)
        
    @property
    def BACKUP_DIR(self):
        '''Get backups directory path'''
        return self._backup_dir
    
    @BACKUP_DIR.setter
    def BACKUP_DIR(self, value):
        '''Set backups directory path'''
        self._backup_dir = value
        self.set('paths.backup_dir', value)
    
    @property
    def USE_STOCKFISH(self):
        '''Get stockfish usage flag'''
        return self._use_stockfish
    
    @USE_STOCKFISH.setter
    def USE_STOCKFISH(self, value):
        '''Set stockfish usage flag'''
        self._use_stockfish = value
        self.set('features.use_stockfish', value)
    
    def __str__(self):
        return f"ConfigManager(logs_dir={self._logs_dir}, data_dir={self._data_dir})"


# For backward compatibility
ConfigurationManager = ConfigManager