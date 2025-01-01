DEPLOYMENT_CONFIG = {
    "platforms": {
        "windows": {
            "installer_type": "exe",
            "build_command": "pyinstaller --onefile --windowed app.py",
            "package_format": "zip",
            "dependencies": ["vcredist", "dotnet-runtime"]
        },
        "macos": {
            "installer_type": "dmg",
            "build_command": "pyinstaller --onefile --windowed app.py",
            "package_format": "zip",
            "code_sign": True,
            "notarize": True
        },
        "linux": {
            "installer_type": "deb",
            "build_command": "pyinstaller --onefile app.py",
            "package_format": "tar.gz",
            "dependencies": ["python3", "qt6-base"]
        },
        "android": {
            "build_tool": "buildozer",
            "package_format": "apk",
            "min_sdk": 21,
            "target_sdk": 33
        },
        "ios": {
            "build_tool": "kivy-ios",
            "package_format": "ipa",
            "min_ios": "13.0",
            "capabilities": ["background-fetch"]
        }
    },
    
    "update_channels": {
        "stable": {
            "auto_update": True,
            "update_frequency": "daily",
            "require_confirmation": True
        },
        "beta": {
            "auto_update": False,
            "update_frequency": "hourly",
            "require_confirmation": True
        }
    },
    
    "distribution": {
        "windows": ["microsoft_store", "direct_download"],
        "macos": ["app_store", "direct_download"],
        "linux": ["snap_store", "apt", "direct_download"],
        "android": ["play_store"],
        "ios": ["app_store"]
    }
} 