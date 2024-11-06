from fastapi import FastAPI, Response
from api.startup.routes import initialize_routes
from fastapi.middleware.cors import CORSMiddleware


from api.startup.mongodb import connect_to_mongo


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


initialize_routes(app)


connect_to_mongo()

# Root route with HTML and inline CSS
@app.get("/", tags=["Root"])
async def root():
    html_content = """
    <html>
        <head>
            <title>Resume Screening API</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <h1 style="color: #4CAF50; text-align: center;">Welcome to the Resume Screening API</h1>
            <p style="text-align: center; font-size: 18px;">
                This API helps screen resumes and extract relevant data for hiring processes.
            </p>
            <div style="margin-top: 30px; text-align: center;">
                <a href="/docs" style="color: #007acc; text-decoration: none; font-size: 18px;">
                    📄 API Documentation
                </a>
            </div>
            <div style="margin-top: 20px; text-align: center; font-size: 16px; color: #333;">
                <p>Status: <span style="color: #4CAF50;">Running</span></p>
            </div>
        </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")