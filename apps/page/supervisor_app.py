import os
from src.utils.redis_handler import RedisHandler
import streamlit as st
import redis


# Initialize Redis connection
@st.cache_resource
def get_redis_supervisor_connection():
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=6379,
            db=2,
            decode_responses=True,  # Automatically decode response bytes to strings
        )
        return r
    except Exception as e:
        st.error(f"Failed to connect to Redis: {e}")
        return None


redis_handler = RedisHandler(get_redis_supervisor_connection())


def main():
    st.title("任務回饋系統")

    # Create tabs for different operations
    create_tab, manage_tab = st.tabs(["新增回饋指令", "管理現有回饋指令"])

    # Tab 1: Create new scenario
    with create_tab:
        st.header("請新增任務回饋指令")

        # Input for new scenario
        new_key = st.text_input("回饋標題（不可重複）", key="new_key")

        new_value = st.text_area("回饋內容", key="new_value", height=600)

        if st.button("新增回饋", type="primary"):
            if new_key and new_value:
                redis_handler.set_value(new_key, new_value)
                if redis_handler.get_value(new_key) == new_value:
                    st.success(f"回饋 '{new_key}' 新增成功！")
                    # Clear inputs after successful addition
                else:
                    st.error("新增回饋失敗。")
            else:
                st.warning("標題和內容都是必填的。")

    # Tab 2: Manage existing scenarios
    with manage_tab:
        st.header("管理現有回饋")

        # Get all scenario keys
        all_keys = redis_handler.get_all_keys()

        if not all_keys:
            st.info("尚未找到任何回饋。請先在「新增回饋」標籤下添加回饋。")
        else:
            selected_key = st.selectbox("選擇回饋", all_keys)

            if selected_key:
                current_value = redis_handler.get_value(selected_key)

                st.subheader("目前回饋詳細資料")
                st.text(f"標題: {selected_key}")
                st.text_area(
                    "內容",
                    value=current_value,
                    key="current_value",
                    height=600,
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("更新回饋"):
                        new_value = st.session_state.current_description
                        if new_value != current_value:
                            if redis_handler.set_value(selected_key, new_value):
                                st.success(f"回饋 '{selected_key}' 更新成功！")
                            else:
                                st.error("更新回饋失敗。")

                with col2:
                    if st.button("刪除回饋", type="primary", use_container_width=True):
                        if redis_handler.delete_key(selected_key):
                            st.success(f"回饋 '{selected_key}' 刪除成功！")
                            st.rerun()  # Refresh the page to update the list
                        else:
                            st.error("刪除回饋失敗。")


if __name__ == "__main__":
    main()
