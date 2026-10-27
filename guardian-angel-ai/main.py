import os

from fastapi import FastAPI, HTTPException
from openai import OpenAI
from pydantic import BaseModel, Field

NEBIUS_API_KEY = os.environ.get("NEBIUS_API_KEY")
NEBIUS_MODEL = os.environ.get("NEBIUS_MODEL")

if not NEBIUS_API_KEY or not NEBIUS_MODEL:
    raise RuntimeError(
        "Set NEBIUS_API_KEY and NEBIUS_MODEL before starting the server."
    )

client = OpenAI(
    base_url="https://api.tokenfactory.nebius.com/v1",
    api_key=NEBIUS_API_KEY,
    timeout=30.0,
)

app = FastAPI(title="Guardian Angel AI")


class SafetyPlanRequest(BaseModel):
    trip_description: str = Field(min_length=1, max_length=1000)


class SafetyPlanResponse(BaseModel):
    plan: str


@app.post("/safety-plan", response_model=SafetyPlanResponse)
def create_safety_plan(request: SafetyPlanRequest):
    try:
        response = client.chat.completions.create(
            model=NEBIUS_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the safety-planning assistant for Guardian Angel. "
                        "Create a short, practical, supportive checklist for the "
                        "user's situation. Do not claim a route or location is safe, "
                        "and do not invent local resources or emergency numbers. "
                        "Do not ask for addresses, phone numbers, or identifying "
                        "details. Do not claim that you have contacted anyone or "
                        "that an alert has been sent. If the user describes an "
                        "immediate emergency, encourage them to contact local "
                        "emergency services or a trusted person if it is safe to "
                        "do so. Respond in plain language."
                    ),
                },
                {
                    "role": "user",
                    "content": request.trip_description,
                },
            ],
                    temperature=0.3,
            max_tokens=600,
            extra_body={
                "chat_template_kwargs": {
                    "enable_thinking": False
                }
            },
        )

        plan = response.choices[0].message.content

        if not plan or not plan.strip():
            raise ValueError("The model returned an empty response.")

        return SafetyPlanResponse(plan=plan.strip())

    except Exception:
        # Do not expose provider errors or credentials to the app.
        raise HTTPException(
            status_code=502,
            detail="Unable to generate a safety plan right now.",
        )
