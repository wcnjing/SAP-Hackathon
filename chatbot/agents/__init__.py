from langchain.agents import create_agent


agent = create_agent(
    model=model,
    prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    response_format=WeatherResponse,
    checkpointer=checkpointer
)

