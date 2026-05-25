from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from chat.routers.chats import router as chats_router
from chat.routers.messages import router as messages_router

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers without prefix to preserve existing endpoint URLs
app.include_router(chats_router)
app.include_router(messages_router)
