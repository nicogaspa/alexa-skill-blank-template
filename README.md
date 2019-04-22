# alexa-skill-blank-template
Blank project template helpful to start developing custom Alexa skills in Python and gain helpful insights.
The developement uses Python ASK SDK and it should help you keeping your code organized, while giving some hints on how to program 
custom intent handlers.

#### ASK CLI
This template is intended to be used together with the ask cli, downloadable here:
https://developer.amazon.com/it/docs/smapi/quick-start-alexa-skills-kit-command-line-interface.html

After the initial setup of the ask cli you can choose wheter to import an already created skill or create a new one. In both cases a new folder 
called as your skill name will be created. You can then use this project as a guideline to continue developing your skill.

The 'pre_deploy_hook.ps1' file will be invoked at the skill deploy using the ask cli and will permorm the following passages:
1. Create a temporary 'lambda_upload' directories under each SOURCE_DIR folder
2. Manage localization and translations
3. Copy the contents of '<SKILL_NAME>/SOURCE_DIR' folder into '<SKILL_NAME>/SOURCE_DIR/lambda_upload'
4. Copy the contents of site packages in $VIRTUALENV created in <SKILL_NAME>/.venv/ folder
5. Update the location of this 'lambda_upload' folder to skill.json for zip and upload

### Start
The starting point is the "lambda_function.py" , this is the main file that will be invoked by the lambda function.

It contains some handlers for built in and custom Intents, that need to be registered.
Intent Handlers should be created in the "intent_handlers" folder and inherit from the BaseHandler that provides connection to DynamoDB, 
in order to store user attributes and skill requests.

### Localization

If a new language needs to be managed, it needs to be added to the skill console.
This creates also a new model in the "models" folder. New utterances for every custom intent has to be provided and
stored in the resources folder.
Then, modify the pre_deploy_hook to manage also the language just added.
This will create, at the next deploy, and empty language folder in the "locales" folder.
Fill the .pot file with the correct messages for the new language and deploy again your code.