from transit_dataloader.dataloader import main as transit_main, lambda_handler as transit_lambda_handler, extract_s3_file_name
from place_dataloader.dataloader import main as places_main


def lambda_handler(event, context):
    """Route incoming trigger events to the appropriate dataloader.

    If the dropped file is named `berkeley.txt` (case-insensitive) we run the places dataloader;
    otherwise we delegate to the transit dataloader handler.
    """
    try:
        try:
            _, _, file_name = extract_s3_file_name(event)
        except Exception:
            # If we can't parse the S3 file name, fall back to transit handler
            return transit_lambda_handler(event, context)

        if file_name and file_name.lower() == "berkeley.txt":
            print("Trigger file is berkeley.txt — running places dataloader")
            places_main()
            return {"statusCode": 200, "body": "Places ingestion completed successfully!"}

        # Default: transit dataloader
        return transit_lambda_handler(event, context)
    except Exception as e:
        print(f"Error during router execution: {e}")
        return {"statusCode": 500, "body": str(e)}