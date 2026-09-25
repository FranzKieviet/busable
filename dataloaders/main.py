from transit_dataloader.dataloader import lambda_handler as transit_lambda_handler, extract_s3_file_name
from place_dataloader.dataloader import main as place_lambda_handler


def lambda_handler(event, context):
    """Route incoming trigger events to the appropriate dataloader.

    If the dropped file is named `berkeley.txt` (case-insensitive) we run the places dataloader;
    otherwise we delegate to the transit dataloader handler.
    """
    try:
        _, _, file_name = extract_s3_file_name(event)

        if file_name and file_name.lower() == "berkeley.txt":
            print("Trigger file is berkeley.txt — running places dataloader")
            return place_lambda_handler()
        else:
            return transit_lambda_handler(event, context)

    except Exception as e:
        print(f"Error during router execution: {e}")
        return {"statusCode": 500, "body": str(e)}