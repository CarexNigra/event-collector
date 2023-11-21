from fastapi import FastAPI, HTTPException, Request, Response, status

app = FastAPI()


@app.post("/store")
async def store_event(request: Request, response: Response) -> None:
    content_type = request.headers.get("content-type", None)
    if content_type != "application/json":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"Unsupported media type {content_type}"
        )
    response.status_code = status.HTTP_204_NO_CONTENT
    # TODO: raise 400 'Bad Request' if the payload has wrong format
