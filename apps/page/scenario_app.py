import os
import streamlit as st
import redis


# Initialize Redis connection
@st.cache_resource
def get_redis_connection():
    try:
        r = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=6379,
            db=0,
            decode_responses=True,  # Automatically decode response bytes to strings
        )
        return r
    except Exception as e:
        st.error(f"Failed to connect to Redis: {e}")
        return None


# Redis operations
def get_all_keys(r):
    if r:
        return r.keys("*")
    return []


def get_value(r, key):
    if r:
        return r.get(key)
    return None


def set_value(r, key, value):
    if r and key and value:
        return r.set(key, value)
    return False


def delete_key(r, key):
    if r and key:
        return r.delete(key)
    return 0


def main():
    st.title("任務情境管理")

    # Initialize Redis connection
    redis_conn = get_redis_connection()

    if not redis_conn:
        st.error("Redis connection failed. Please check your Redis server.")
        return

    # Create tabs for different operations
    create_tab, manage_tab = st.tabs(["新增情境", "管理現有情境"])

    # Tab 1: Create new scenario
    with create_tab:
        st.header("請新增任務情境")

        # Input for new scenario
        new_title = st.text_input("情境標題（不可重複）", key="new_title")

        if new_title in get_all_keys(redis_conn):
            st.warning("情境標題已存在，請使用其他標題。")
        else:
            new_description = st.text_area(
                "情境內容", key="new_description", height=600
            )

            if st.button("新增情境", type="primary"):
                if new_title and new_description:
                    if set_value(redis_conn, new_title, new_description):
                        st.success(f"情境 '{new_title}' 新增成功！")
                        # Clear inputs after successful addition
                        st.session_state.new_title = ""
                        st.session_state.new_description = ""
                    else:
                        st.error("新增情境失敗。")
                else:
                    st.warning("標題和內容都是必填的。")

    # Tab 2: Manage existing scenarios
    with manage_tab:
        st.header("管理現有情境")

        # Get all scenario keys
        all_keys = get_all_keys(redis_conn)

        if not all_keys:
            st.info("尚未找到任何情境。請先在「新增情境」標籤下添加情境。")
        else:
            selected_key = st.selectbox("選擇情境", all_keys)

            if selected_key:
                current_value = get_value(redis_conn, selected_key)

                st.subheader("目前情境詳細資料")
                st.text(f"標題: {selected_key}")
                st.text_area(
                    "內容",
                    value=current_value,
                    key="current_description",
                    height=150,
                )

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("更新情境"):
                        new_value = st.session_state.current_description
                        if new_value != current_value:
                            if set_value(redis_conn, selected_key, new_value):
                                st.success(f"情境 '{selected_key}' 更新成功！")
                            else:
                                st.error("更新情境失敗。")

                with col2:
                    if st.button("刪除情境", type="primary", use_container_width=True):
                        if delete_key(redis_conn, selected_key):
                            st.success(f"情境 '{selected_key}' 刪除成功！")
                            st.rerun()  # Refresh the page to update the list
                        else:
                            st.error("刪除情境失敗。")


if __name__ == "__main__":
    main()
