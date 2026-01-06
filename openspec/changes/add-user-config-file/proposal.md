# Change: Add User Configuration File Support

## Why
Currently, all configurable values (output paths, email settings, SMTP configuration, GPG settings, policy thresholds, version check settings) are hardcoded in the script's CONFIGURATION section (lines 30-72 in linux_health_check.py). This makes it difficult for users to:

1. Customize settings without modifying the script directly
2. Maintain their configuration when updating to newer script versions
3. Version control their specific settings separately from the script
4. Deploy multiple configurations for different environments

A separate, git-ignored configuration file would allow users to maintain their settings independently while easily updating the main script.

## What Changes
- Add support for loading configuration from an external `health_check_config.py` file
- Create an example configuration file (`health_check_config.example.py`) with all available settings documented
- Load user config from the same directory as the script
- Fall back to hardcoded defaults if config file doesn't exist
- Add `health_check_config.py` to `.gitignore` to prevent overwriting user configurations during updates
- Maintain backward compatibility with existing hardcoded defaults

## Impact
- Affected specs: New capability `configuration` (config-management)
- Affected code: 
  - `linux_health_check.py` (CONFIGURATION section, lines 30-72)
  - `.gitignore` (add config file exclusion)
  - New files: `health_check_config.example.py`
- **BREAKING**: None - fully backward compatible
- Users will need to create their own config file to customize settings (example file provided)

## Recommendations for Improvement
1. **Config File Format**: Use Python file format (`.py`) rather than JSON/YAML/INI for several reasons:
   - No additional dependencies required (maintains stdlib-only constraint)
   - Familiar syntax for Python users
   - Allows comments for documentation
   - Type hints can be used
   - Can include computed values if needed

2. **Config File Location**: Place in same directory as script (not in separate config directory) because:
   - Script is designed to be self-contained and portable
   - Simplifies deployment (just copy both files)
   - No need to handle multiple search paths
   - Matches the project's "single utility" design goal

3. **Validation**: Add basic config validation to:
   - Check required settings are present
   - Validate types (e.g., thresholds are integers)
   - Warn about unknown settings
   - Provide helpful error messages for misconfiguration

4. **Documentation**: Include comprehensive inline documentation in example config showing:
   - Purpose of each setting
   - Valid value ranges
   - Examples for common scenarios
   - Security considerations (e.g., storing SMTP passwords)

5. **Environment Variable Override**: Consider allowing environment variables to override config file settings for:
   - CI/CD pipelines
   - Container deployments
   - Temporary overrides without editing files
   - Priority: ENV > Config File > Hardcoded Defaults

6. **Security Hardening**:
   - Warn if config file has world-readable permissions (contains credentials)
   - Document secure storage options (e.g., using GPG-encrypted config)
   - Consider supporting external secret management in future versions

7. **Migration Path**: Provide migration instructions showing:
   - How to extract current settings from script
   - How to test config before committing
   - How to validate config file syntax

## Alternatives Considered
- **JSON/YAML/TOML**: Rejected due to requiring external dependencies
- **Environment variables only**: Rejected as too cumbersome for many settings
- **Embedded in home directory** (e.g., `~/.health_check_config`): Rejected to maintain script portability and single-directory deployment
