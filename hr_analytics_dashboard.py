    "Simulated Workforce Analytics"
)



# Generative AI HR Assistant

from google import genai

st.divider()

st.header("AI HR Assistant")

st.write("""
Ask questions about workforce trends, compensation,
employee departures, and HR strategy using generative AI.
""")

st.caption(
    "Powered by Google Gemini. Only use simulated data. "
    "AI responses should be reviewed by a human."
)

question = st.text_area(
    "Ask a question about your workforce",
    placeholder="What workforce trends should HR leadership investigate?",
    max_chars=500
)

if st.button("Generate AI Insights"):

    if not question.strip():
        st.warning("Please enter a question.")

    elif "GEMINI_API_KEY" not in st.secrets:
        st.error("AI API key has not been configured.")

    else:
        try:
            client = genai.Client(
                api_key=st.secrets["GEMINI_API_KEY"]
            )

            workforce_context = summary.round(2).to_string(
                index=False
            )

            prompt = f"""
You are an HR workforce analytics assistant.

Analyze the following simulated, aggregated workforce data:

{workforce_context}

User question:
{question}

Provide:
1. Key findings supported by the data.
2. Potential HR recommendations.
3. Additional information HR should collect.

Do not invent statistics.
Do not assume correlation means causation.
Do not make individual employment decisions.
Treat departure share as descriptive, not annual turnover.
Acknowledge ties and limitations.
Keep your response professional and concise.
"""

            with st.spinner("Analyzing workforce data..."):

                models = [
                    m.name for m in client.models.list()
                    if m.name
                    and "flash" in m.name.lower()
                    and "generateContent" in (
                        m.supported_actions or []
                    )
                    and not any(
                        x in m.name.lower()
                        for x in [
                            "preview", "experimental",
                            "image", "audio", "tts"
                        ]
                    )
                ]

                if not models:
                    st.warning("No compatible AI model found.")
                else:
                    model = sorted(models, reverse=True)[0]

                    response = client.models.generate_content(
                        model=model,
                        contents=prompt
                    )

                    if response.text:
                        st.subheader("AI Workforce Analysis")
                        st.markdown(response.text)

                        st.download_button(
                            "Download AI Analysis",
                            data=response.text,
                            file_name="AI_HR_Analysis.txt",
                            mime="text/plain"
                        )
                    else:
                        st.warning("No text response was generated.")

        except Exception as e:
            st.error(f"AI request failed: {type(e).__name__}")
            st.write("Error code:", getattr(e, "code", "Unknown"))
