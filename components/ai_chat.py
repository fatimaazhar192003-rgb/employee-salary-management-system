"""
ai_chat.py - AI Assistant Chat Interface for PayrollPro AI
"""
import streamlit as st
from datetime import datetime


def render_ai_chat(db, orchestrator, user_role):
    """Interactive AI assistant for natural language payroll queries."""
    st.markdown("## 🤖 AI Payroll Assistant")
    st.markdown("Ask me anything about payroll, attendance, analytics, or HR data.")

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": (
                    "👋 Hello! I'm **PayrollPro AI**, your intelligent payroll assistant.\n\n"
                    "I can help you with:\n"
                    "- 💰 **Payroll queries** — \"Show payroll summary for October\"\n"
                    "- 👥 **Employee info** — \"How many employees are in Engineering?\"\n"
                    "- 📅 **Attendance** — \"Who was absent most this month?\"\n"
                    "- 📊 **Analytics** — \"What's the total payroll this year?\"\n"
                    "- 🔧 **Actions** — \"Process payroll for November 2026\"\n\n"
                    "How can I help you today?"
                ),
                "timestamp": datetime.now().strftime("%H:%M"),
            }
        ]

    # Render chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            st.caption(msg.get("timestamp", ""))

    # Input
    user_input = st.chat_input("Ask me anything about your payroll data…")

    if user_input:
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M"),
        })

        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    response = orchestrator.process_query(
                        query=user_input,
                        db=db,
                        user_role=user_role,
                        username=st.session_state.get("username", "user"),
                    )

                    if isinstance(response, dict):
                        answer = response.get("answer", response.get("result", str(response)))
                        # Log AI execution
                        try:
                            db.log_ai_execution(
                                username=st.session_state.get("username", "user"),
                                user_query=user_input,
                                agent_used=response.get("agent_used", "orchestrator"),
                                task_type=response.get("task_type", "query"),
                                status=response.get("status", "success"),
                                result=answer,
                            )
                        except Exception:
                            pass
                    else:
                        answer = str(response)

                except Exception as e:
                    answer = f"⚠️ I encountered an error: {e}\n\nPlease try rephrasing your question."

                st.markdown(answer)
                now = datetime.now().strftime("%H:%M")
                st.caption(now)

                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": answer,
                    "timestamp": now,
                })

    # Sidebar controls
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🤖 AI Controls")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

        st.markdown("**Quick Queries:**")
        quick_queries = [
            "Show dashboard summary",
            "List all departments",
            "Who has pending leaves?",
            "Total payroll this month",
            "Top 5 highest earners",
        ]
        for q in quick_queries:
            if st.button(q, use_container_width=True, key=f"quick_{q}"):
                st.session_state.chat_messages.append({
                    "role": "user",
                    "content": q,
                    "timestamp": datetime.now().strftime("%H:%M"),
                })
                st.rerun()
