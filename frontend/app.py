import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"


def main():
    st.set_page_config(
        page_title="AI-Powered GitHub Issue Assistant",
        layout="centered",
    )

    st.title("🔎 AI-Powered GitHub Issue Assistant")
    st.markdown(
        """
Analyze a GitHub issue using an AI agent.

**Steps:**
1. Enter a public GitHub repository URL.
2. Enter a valid issue number.
3. Click **Analyze Issue**.
        """
    )

    with st.form("issue_form"):
        repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/facebook/react",
        )
        issue_number = st.number_input(
            "Issue Number",
            min_value=1,
            step=1,
        )
        submitted = st.form_submit_button("Analyze Issue")

    if submitted:
        if not repo_url:
            st.error("Please provide a repository URL.")
            return

        with st.spinner("Analyzing issue with AI..."):
            try:
                payload = {
                    "repo_url": repo_url,
                    "issue_number": int(issue_number),
                }
                resp = requests.post(f"{API_BASE_URL}/analyze", json=payload, timeout=60)
            except Exception as e:
                st.error(f"Failed to call backend: {e}")
                return

        if resp.status_code != 200:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            st.error(f"Backend error ({resp.status_code}): {detail}")
            return

        data = resp.json()

        st.success("Analysis complete!")

        # Pretty display
        st.subheader("Structured Analysis")

        st.markdown("### 📝 Summary")
        st.write(data.get("summary", ""))

        st.markdown("### 🏷 Type")
        st.code(data.get("type", ""), language="text")

        st.markdown("### ⚠️ Priority Score")
        st.write(data.get("priority_score", ""))

        st.markdown("### 🔖 Suggested Labels")
        labels = data.get("suggested_labels", [])
        if labels:
            st.write(", ".join(labels))
        else:
            st.write("No labels suggested.")

        st.markdown("### 👥 Potential Impact")
        st.write(data.get("potential_impact", ""))

        st.markdown("### 📦 Raw JSON")
        import json
        st.code(json.dumps(data, indent=4), language="json")


        # Extra: copyable JSON
        st.markdown("### 📋 Copyable JSON")
        st.code(data, language="json")


if __name__ == "__main__":
    main()
