import os

from transit_dataloader.dataloader import lambda_handler as transit_lambda_handler, extract_s3_file_name
from place_dataloader.dataloader import main as place_lambda_handler, PLACE_REGIONS


def lambda_handler(event, context):
    """Route incoming trigger events to the appropriate dataloader.

    If the dropped file is named after a places region (e.g. `bay-area.txt`, `central.txt`, `socal.txt`,
    case-insensitive) we run the places dataloader for that region; otherwise we delegate to the transit dataloader handler.
    """
    try:
        _, _, file_name = extract_s3_file_name(event)
        region = os.path.splitext(file_name or "")[0].lower()

        if region in PLACE_REGIONS:
            print(f"Trigger file is {file_name} — running places dataloader for region {region}")
            return place_lambda_handler(region)
        else:
            return transit_lambda_handler(event, context)

    except Exception as e:
        print(f"Error during router execution: {e}")
        return {"statusCode": 500, "body": str(e)}