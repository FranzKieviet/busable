from transit_dataloader.dataloader import main as transit_dataloader_main

def lambda_handler(event, context):
    """
    AWS Lambda entry point.
    - event: Contains payload data passed to the invocation.
    - context: Contains runtime information about the execution.
    """
    try:
        transit_dataloader_main()
        return {
            "statusCode": 200,
            "body": "Ingestion completed successfully!"
        }
    except Exception as e:
        print(f"Error during execution: {e}")
        return {
            "statusCode": 500,
            "body": str(e)
        }