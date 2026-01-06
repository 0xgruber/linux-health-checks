## ADDED Requirements

### Requirement: External Configuration File Support
The system SHALL support loading user-defined configuration from an external Python configuration file located in the same directory as the main script.

#### Scenario: Config file exists with valid settings
- **WHEN** a `health_check_config.py` file exists in the script directory with valid configuration
- **THEN** the script SHALL load configuration values from that file
- **AND** the script SHALL use loaded values instead of hardcoded defaults
- **AND** the script SHALL log which configuration source was used

#### Scenario: Config file does not exist
- **WHEN** no `health_check_config.py` file exists in the script directory
- **THEN** the script SHALL use hardcoded default configuration values
- **AND** the script SHALL execute normally without errors
- **AND** backward compatibility SHALL be maintained

#### Scenario: Config file has syntax errors
- **WHEN** a `health_check_config.py` file exists but contains Python syntax errors
- **THEN** the script SHALL log a clear error message indicating the config file is invalid
- **AND** the script SHALL fall back to hardcoded default values
- **AND** the script SHALL continue execution without crashing

#### Scenario: Config file has partial configuration
- **WHEN** a `health_check_config.py` file exists with only some configuration values defined
- **THEN** the script SHALL use values from the config file where present
- **AND** the script SHALL use hardcoded defaults for missing values
- **AND** the script SHALL execute successfully

### Requirement: Configuration Value Validation
The system SHALL validate configuration values loaded from external configuration files to ensure they are within acceptable ranges and types.

#### Scenario: Valid configuration values
- **WHEN** configuration values are within valid ranges and correct types
- **THEN** the script SHALL accept and use those values
- **AND** no validation warnings SHALL be logged

#### Scenario: Invalid threshold percentages
- **WHEN** threshold values (e.g., FILESYSTEM_WARNING_THRESHOLD) are outside the range 0-100
- **THEN** the script SHALL log a warning about invalid threshold
- **AND** the script SHALL fall back to default value for that setting
- **AND** execution SHALL continue

#### Scenario: Invalid type for configuration value
- **WHEN** a configuration value has incorrect type (e.g., string instead of integer)
- **THEN** the script SHALL log a clear type error message
- **AND** the script SHALL fall back to default value for that setting
- **AND** execution SHALL continue

#### Scenario: Unknown configuration variables
- **WHEN** the config file contains variables not recognized by the script
- **THEN** the script SHALL log a warning about unknown configuration variables
- **AND** the script SHALL ignore unknown variables
- **AND** execution SHALL continue normally

### Requirement: Environment Variable Override
The system SHALL support overriding configuration values via environment variables with priority: environment variables > config file > hardcoded defaults.

#### Scenario: Environment variable overrides config file
- **WHEN** an environment variable is set for a configuration value
- **AND** the same value exists in the config file
- **THEN** the environment variable value SHALL take precedence
- **AND** the script SHALL log that an environment variable override was used

#### Scenario: Environment variable with no config file
- **WHEN** an environment variable is set for a configuration value
- **AND** no config file exists
- **THEN** the environment variable value SHALL override the hardcoded default
- **AND** the script SHALL execute with the overridden value

#### Scenario: No overrides present
- **WHEN** no environment variables are set
- **AND** a config file exists with values
- **THEN** config file values SHALL be used
- **AND** environment defaults SHALL not interfere

### Requirement: Example Configuration File
The system SHALL provide a comprehensive example configuration file that documents all available settings.

#### Scenario: Example file provided
- **WHEN** the repository is cloned or the script is downloaded
- **THEN** a `health_check_config.example.py` file SHALL be present
- **AND** the file SHALL contain all configurable settings with inline documentation
- **AND** the file SHALL include value ranges, types, and usage examples

#### Scenario: User creates config from example
- **WHEN** user copies `health_check_config.example.py` to `health_check_config.py`
- **AND** user modifies values as needed
- **THEN** the script SHALL load the user's configuration
- **AND** the user SHALL be able to update the script without losing configuration

### Requirement: Git Ignore Configuration File
The system repository SHALL exclude user configuration files from version control to prevent overwriting user settings during updates.

#### Scenario: Config file not tracked by git
- **WHEN** a user creates `health_check_config.py` in their working directory
- **THEN** git SHALL ignore the file (via .gitignore)
- **AND** the file SHALL not be committed to version control
- **AND** the file SHALL not be overwritten during git pull

#### Scenario: Example file is tracked
- **WHEN** the repository contains `health_check_config.example.py`
- **THEN** the example file SHALL be tracked by git
- **AND** updates to the example SHALL be pulled during git updates
- **AND** the example SHALL reflect current available configuration options

### Requirement: Security Validation
The system SHALL warn users when configuration files contain sensitive information and have insecure file permissions.

#### Scenario: Config file is world-readable with credentials
- **WHEN** `health_check_config.py` exists with mode 0644 or more permissive
- **AND** the config contains SMTP credentials or GPG settings
- **THEN** the script SHALL log a security warning
- **AND** the script SHALL recommend restricting permissions to 0600
- **AND** execution SHALL continue with the warning

#### Scenario: Config file has restricted permissions
- **WHEN** `health_check_config.py` exists with mode 0600
- **THEN** no security warning SHALL be logged
- **AND** the script SHALL load configuration normally

### Requirement: Configuration Discovery
The system SHALL locate the configuration file in the same directory as the executing script.

#### Scenario: Script and config in same directory
- **WHEN** both `linux_health_check.py` and `health_check_config.py` are in the same directory
- **THEN** the script SHALL successfully locate and load the config file
- **AND** the relative path resolution SHALL work correctly

#### Scenario: Script executed from different directory
- **WHEN** the script is executed from a different working directory (e.g., `/usr/local/bin/linux_health_check.py`)
- **AND** the config file is in the same directory as the script
- **THEN** the script SHALL locate the config file using the script's directory
- **AND** configuration SHALL load successfully regardless of execution path

### Requirement: Backward Compatibility
The system SHALL maintain full backward compatibility with existing deployments that do not use configuration files.

#### Scenario: No configuration file present on existing deployment
- **WHEN** the script is updated but no config file is created
- **THEN** all behavior SHALL remain identical to previous versions
- **AND** all default values SHALL match historical defaults
- **AND** no functionality SHALL be broken

#### Scenario: Configuration values match defaults
- **WHEN** a config file exists with values identical to hardcoded defaults
- **THEN** the script behavior SHALL be identical to running without a config file
- **AND** no differences in output or logging SHALL occur
