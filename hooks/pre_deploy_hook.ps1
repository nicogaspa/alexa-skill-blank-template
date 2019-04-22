# Powershell script for ask-cli pre-deploy hook for Python
# Script Usage: pre_deploy_hook.ps1 <SKILL_NAME> <DO_DEBUG> <TARGET>

# SKILL_NAME is the preformatted name passed from the CLI, after removing special characters.
# DO_DEBUG is boolean value for debug logging
# TARGET is the deploy TARGET provided to the CLI. (eg: all, skill, lambda etc.)

# Run this script under the skill root folder

# The script does the following:
#  - Create a temporary 'lambda_upload' directories under each SOURCE_DIR folder
#  - Copy the contents of '<SKILL_NAME>/SOURCE_DIR' folder into '<SKILL_NAME>/SOURCE_DIR/lambda_upload'
#  - Copy the contents of site packages in $VIRTUALENV created in <SKILL_NAME>/.venv/ folder
#  - Update the location of this 'lambda_upload' folder to skill.json for zip and upload

param(
    [string] $SKILL_NAME,
    [bool] $DO_DEBUG = $False,
    [string] $TARGET = "all"
)

if ($TARGET -eq "all" -Or $TARGET -eq "lambda") {

    # Ignoring the DO_DEBUG parameter that would have commented these lines as they are pretty useful
    Write-Output "########################################################"
    Write-Output "#####               pre-deploy hook                #####"
    Write-Output "########################################################"

    $ALL_SOURCE_DIRS = Get-Content -Path "skill.json" | select-string  -Pattern "sourceDir" -CaseSensitive
    Foreach ($SOURCE_DIR in $ALL_SOURCE_DIRS) {

        # -------------- Step 1: Decide source path and upload path ----------------------------------------------------
        $FILTER_SOURCE_DIR = $SOURCE_DIR -replace "`"", "" -replace "\s", "" -replace ",","" -replace "sourceDir:", ""
        if ($FILTER_SOURCE_DIR.endsWith("/lambda_upload")) {
            $UPLOAD_DIR_PATH = $FILTER_SOURCE_DIR
            $CODE_PATH = $FILTER_SOURCE_DIR.replace("/lambda_upload", "")
        } else {
            $UPLOAD_DIR_PATH = $FILTER_SOURCE_DIR + "/lambda_upload"
            $CODE_PATH = $FILTER_SOURCE_DIR
        }


        # -------------- Step 2: Create empty lambda_upload folder -----------------------------------------------------
        Write-Output "#         Creating empty lambda_upload folder          #"
        Remove-Item -Recurse -Force $UPLOAD_DIR_PATH -ErrorAction Ignore
        New-Item -Force $UPLOAD_DIR_PATH -ItemType "directory" 2>&1 | Out-Null


        # -------------- Step 3: Extract the messages and generate message catalog -------------------------------------
        Write-Output "#        Internationalization of Python skill          #"
        # Creates the skill.pot file (portable object template)
        Invoke-Expression ".venv\Scripts\pybabel extract $CODE_PATH\alexa\data.py -o $CODE_PATH\locales\data.pot --no-wrap --omit-header --add-comments=NOTE --no-location" 2>&1 | Out-Null
        # Initialize every locale with a .po file if it doesn't exists, translating every message in the skill.pot
        # TODO change here the languages supported by your skill
        Foreach ($LOCALE in "it_IT", "en_US", "en_AU", "en_CA", "en_GB", "en_IN") {
            $LOCALEDIR = $LOCALE -replace "_","-"
            if (!(Test-Path "$CODE_PATH\locales\$LOCALEDIR\LC_MESSAGES\data.po" -PathType Leaf)) {
                Write-Output "#           $LOCALE .po file absent, creating it         #"
                Invoke-Expression ".venv\Scripts\pybabel init -i $CODE_PATH\locales\data.pot -l $LOCALE -o $CODE_PATH\locales\$LOCALEDIR\LC_MESSAGES\data.po" 2>&1 | Out-Null
            }else{
                Write-Output "#           $LOCALE .po file present, updating it        #"
                Invoke-Expression ".venv\Scripts\pybabel update -i $CODE_PATH\locales\data.pot -l $LOCALE -o $CODE_PATH\locales\$LOCALEDIR\LC_MESSAGES\data.po" 2>&1 | Out-Null
            }
            # Translate the .po files in .mo files (machine objects)
            Invoke-Expression ".venv\Scripts\pybabel compile -i $CODE_PATH\locales\$LOCALEDIR\LC_MESSAGES\data.po -l $LOCALE -o $CODE_PATH\locales\$LOCALEDIR\LC_MESSAGES\data.mo" 2>&1 | Out-Null
        }

        # -------------- Step 4: Copy source code in sourceDir to lambda_upload ----------------------------------------
        Write-Output "# Copying files from sourceDir to lambda_upload folder #"
        $EXCLUDE_PATH = Resolve-Path -Path ((pwd).Path + "/" + $UPLOAD_DIR_PATH)
        robocopy $CODE_PATH $UPLOAD_DIR_PATH /s /e /ndl /XD $EXCLUDE_PATH 2>&1 | Out-Null


        # -------------- Step 5: Find virtual environment site packages, copy contents to lambda_upload ----------------
        Write-Output "#     Fill lambda_upload folder with .venv packets     #"
        # $SITE = $(.venv\Scripts\python -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")
        Copy-Item ".venv\skill_env\*" -Destination $UPLOAD_DIR_PATH -Recurse -force


        # -------------- Step 6: Update the "manifest.apis.custom.endpoint.sourceDir" value in skill.json if necessary -
        if (!$FILTER_SOURCE_DIR.endsWith("/lambda_upload")) {
            $RAW_SOURCE_DIR_LINE = "`"sourceDir`": `"$FILTER_SOURCE_DIR`""
            $NEW_SOURCE_DIR_LINE = "`"sourceDir`": `"$UPLOAD_DIR_PATH`""
            (Get-Content "skill.json").replace($RAW_SOURCE_DIR_LINE, $NEW_SOURCE_DIR_LINE) | Set-Content "skill.json"
        }

    }

    Write-Output "########################################################"
    Write-Output "#####                   END hook                   #####"
    Write-Output "########################################################"

    exit 0
}