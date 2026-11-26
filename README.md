# hyperos-accessibility-fix
Stop HyperOS from randomly disabling accessibility services

## What's happening
On Android, when an accessibility app is force-stopped via `ActivityManager`, the [accessibility permission of the app is stripped](https://cs.android.com/android/platform/superproject/+/android-16.0.0_r4:frameworks/base/services/accessibility/java/com/android/server/accessibility/AccessibilityManagerService.java;drc=7f9ce6b127e5d17d7a2ccef1ccc21db212f60084;l=1050).

```java
boolean onPackagesForceStoppedLocked(String[] packages, AccessibilityUserState userState) {
    final Set<String> packageSet = Set.of(packages);
    
    final ArrayList<ComponentName> continuousServices = userState.mInstalledServices.stream()
            .filter(s -> (s.flags & FLAG_REQUEST_ACCESSIBILITY_BUTTON) == FLAG_REQUEST_ACCESSIBILITY_BUTTON)
            .map(AccessibilityServiceInfo::getComponentName)
            .filter(name -> packageSet.contains(name.getPackageName()))
            .collect(Collectors.toCollection(ArrayList::new));

    final boolean enabledServicesChanged = userState.mEnabledServices.removeIf(comp -> {
        if (packageSet.contains(comp.getPackageName())) {
            userState.getBindingServicesLocked().remove(comp);
            userState.getCrashedServicesLocked().remove(comp);
            return true;
        }
        return false;
    });

    if (enabledServicesChanged) {
        persistComponentNamesToSettingLocked(
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
            userState.mEnabledServices, userState.mUserId);
    }
}
    ...
```

And HyperOS is hardcoded to trigger a force-stop (not a kill) on 
certain events like when the user is entering Ultra Battery Saver (`LockScreenClean`),
and others:

```log
<ultra battery saver was enabled>
I ActivityManager: Force stopping com.urbandroid.lux appid=10415 user=0: LockScreenClean
D ActivityManager: Force removing proc 8855:com.urbandroid.lux:background/u0a415 (com.urbandroid.lux:background/10415)
```

## How it works
- This module installs a background script that monitors the `logcat` stream for accessibility update events 
with minimal system overhead.

- On boot, it checks what accessibility services are enabled, and writes them to `a11y_watchlist.txt`. It also listens for signs of manual 
configuration changes (done by user in settings) and updates the watchlist automatically.
 
- When an accessibility update event is detected, the background script first checks if the device is in the Settings app (as mentioned above).
If not, the background script performs a verification of enabled accessibility services against the local `a11y_watchlist.txt`.
And if the list doesn't match up, the changes are reverted instantly.

- This background script also runs at `OOM` score `-800` to prevent `LMKD` from killing it in the background. And if it still gets killed under memory pressure,
another (monitor) script (that runs at `-900`) is running in background to restart it (provided it didn't get killed aswell lol)

## Note
- When Ultra Battery Saver is turned on, the accessibility services will still keep running in the background
- Force stopping an app via App Manager will not (permanently) remove it's accessibility permission anymore.
So be careful at what you enable
- You may ask why did i use background scripts and not `zygisk`/`xposed`. That's because these two frameworks cause
a range of problems for me, so i decided to follow this no-requirement approach instead.

## How do i build this from source?
Just run the build script at the root of the repo. The minimum requirement for this is `~python3.10`:

```shell
python build.py
```
```shell
# Created /home/user/module/build/hyperos-accessibility-fix-x.x.x.zip
# Created /home/user/module/build/hyperos-accessibility-fix.zip (for permalink purposes)
```

## Installation:
- [Download the module archive here](https://github.com/chkndrp/hyperos-accessibility-fix/releases/latest/download/hyperos-accessibility-fix.zip). There is also a [mirror at SourceForge](https://sourceforge.net/projects/hyperos-accessibility-fix/)
- Flash it in magisk app, or using command line

## Requirements
- HyperOS 1.0+ (or any A14+ system)
- KernelSU 1.0.2+ or Magisk 28.0+
