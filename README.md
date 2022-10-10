## phoneLookup Lambda Function

## Structure

- Connect: Rasa Inbound Flow
  - Lex: lexToRasaBot:TestBotAlias
    - Lambda: lexToRasaRIS:$LATEST

## Example Projects

- https://github.com/cloudacademy/aws-lexv2-chatbot
- https://support.cognigy.com/hc/en-us/articles/360016863379-Amazon-Connect#h_01FWE56FFP2FTNR4H4XD3PRQRA

```
pip install --upgrade --target ./package pynamodb
FUNCTION="phoneLookup"
rm function.zip
cd package
zip -r9 ../function.zip .
cd ..
zip -g function.zip lambda_function.py
aws lambda update-function-code --function-name $FUNCTION --zip-file fileb://function.zip
```

```sh
aws iam create-role --role-name lambda-ex --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
aws lambda create-function --function-name lexToRasaRIS --zip-file fileb://function.zip --handler lambda_function.lamdba_handler --runtime python3.8 --role arn:aws:iam::866115775882:role/lambda-ex
FUNCTION="lexToRasaRIS"
aws lambda update-function-configuration --function-name $FUNCTION --environment Variables="{MQTT_HOST=gstephens.org,MQTT_USER=iot,MQTT_PASS=my7Q7XeiHW5P,RASA_HOST=risbot.rasabot.us}"
aws lambda update-function-configuration --function-name $FUNCTION --environment Variables="{MQTT_HOST=gstephens.org,MQTT_USER=iot,MQTT_PASS=my7Q7XeiHW5P,RASA_HOST=risbot.rasabot.us}"
```

```sh
FUNCTION="lexExample"
aws lambda update-function-configuration --function-name $FUNCTION --environment Variables="{MQTT_HOST=gstephens.org,MQTT_USER=iot,MQTT_PASS=my7Q7XeiHW5P,RASA_HOST=risbot.rasabot.us}"
```

## Local Testing

- [python-lambda-local](https://github.com/HDE/python-lambda-local)
- [pynamodb](https://github.com/pynamodb/PynamoDB)

```sh
export RASA_HOST=risbot.rasabot.us
python-lambda-local -l package/ -f lambda_handler -t 5 lambda_function.py event.json
```

## Connect Attributes

- [Cheat Sheet](https://www.connectdemo.com/references/attributeCheatSheet.html)
- [Amazon Connect & Lex Blog](https://docs.aws.amazon.com/connect/latest/adminguide/amazon-lex.html)
- [Troubleshoot Flow Errors](https://catalog.workshops.aws/troubleshooting-contact-flow-errors/en-US)
- [Get customer input](https://docs.aws.amazon.com/connect/latest/adminguide/get-customer-input.html) block

## Lex v2

- [Lambda Fallback](https://docs.aws.amazon.com/lexv2/latest/dg/built-in-intent-fallback.html)
- [Understanding New Flows](https://docs.aws.amazon.com/lexv2/latest/dg/understanding-new-flows.html)
- [Invoke a Dialog Code Hook](https://docs.aws.amazon.com/lexv2/latest/dg/paths-code-hook.html)
- [Configure Logs](https://docs.aws.amazon.com/lexv2/latest/dg/conversation-logs-configure.html)
- [Configure Lambda Function](https://docs.aws.amazon.com/lexv2/latest/dg/lambda.html)

## Configure Dialog Code Hook

- In the intent editor, you turn on Lambda functions in the in the advanced options in the Dialog code hook section for each response in the editor.

There are two steps to using a Lambda function. 
- First, you must activate the dialog code hook at any point in the conversation.
- Second, you must set the next step in the conversation to use the dialog code hook.

## Configure Lambda Function in Lex

To **choose a Lambda function** to use with a bot alias

- Open the Amazon Lex console at https://console.aws.amazon.com/lexv2/.
- From the list of bots, choose the name of the bot that you want to use.
- From Create versions and aliases for deployment, choose View aliases.
- From the list of aliases, choose the name of the **alias** that you want to use.
- From the list of supported languages, **choose the language** that the Lambda function is used for.
- Choose the name of the Lambda function to use, then choose the version or alias of the function.
- Choose Save to save your changes.

### Event From **Connect** to **Lex** bot

```json
{
    "timestamp": "2022-09-05T03:11:42.173Z",
    "messageVersion": "2.0",
    "dialogEventLogs": [
        {
            "nextStep": {
                "dialogAction": {
                    "type": "EndConversation"
                }
            },
            "dialogStepLabel": "Intent/FallbackIntent/StartIntent"
        }
    ],
    "transcriptions": [
        {
            "transcription": "hello",
            "transcriptionConfidence": 1,
            "resolvedContext": {
                "intent": "FallbackIntent"
            },
            "resolvedSlots": {}
        }
    ],
    "requestId": "11b32b09-ec7b-4ceb-a4e5-a92cf2c283ac",
    "sessionId": "929e9aa7-155b-471b-b68d-45c8da484292",
    "requestAttributes": {
        "x-amz-lex:accept-content-types": "PlainText"
    },
    "inputMode": "Text",
    "operationName": "RecognizeText",
    "developerOverride": false,
    "sessionState": {
        "sessionAttributes": {
            "PhoneNumber": "",
            "ContactId": "153f9ffd-6cb1-4bae-9e58-2e0675751786",
            "TextToSpeechVoiceId": "Joanna",
            "Channel": "CHAT"
        },
        "originatingRequestId": "11b32b09-ec7b-4ceb-a4e5-a92cf2c283ac",
        "intent": {
            "name": "FallbackIntent",
            "state": "ReadyForFulfillment",
            "slots": {},
            "confirmationState": "None"
        },
        "dialogAction": {
            "type": "Close"
        }
    },
    "interpretations": [
        {
            "intent": {
                "name": "FallbackIntent",
                "state": "ReadyForFulfillment",
                "slots": {},
                "confirmationState": "None"
            }
        },
        {
            "nluConfidence": "0.63",
            "intent": {
                "name": "NewIntent",
                "slots": {}
            }
        }
    ],
    "utteranceContext": {},
    "inputTranscript": "hello",
    "missedUtterance": true,
    "bot": {
        "name": "lexToRasaBot",
        "version": "DRAFT",
        "id": "K61NSOGZCS",
        "aliasName": "TestBotAlias",
        "aliasId": "TSTALIASID",
        "localeId": "en_US"
    }
}
```

## Lambda event from Lex

```json
{
  "inputTranscript": "Hi",
  "outputDialogMode": "Text",
  "userId": "Greg",
  "invocationSource": "FulfillmentCodeHook",
  "messageVersion": "1.0",
  "currentIntent": {
    "name": "TestIntent",
    "nluIntentConfidenceScore": ".98"
  },
  "bot": {
    "name": "FallbackIntent",
    "alias": "$LATEST",
    "version": "$LATEST"
  }
}
```
