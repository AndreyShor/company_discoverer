from calendar import c
from sympy import false
from fastapi.middleware.cors import CORSMiddleware # type: ignore

class SettingsAPI: 

    def __init__(self, app, corsFlag: bool = false):
        self.app = app

        if corsFlag:
            self.turn_on_cors()

    def turn_on_cors(self):
        """ Enable CORS for the FastAPI application """
        
        # CORS settings
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            ], # or ["*"] for all origins (dev only)
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


