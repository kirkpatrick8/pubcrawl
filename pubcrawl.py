        else:
            st.markdown(
                "<div class='locked-achievement'>Locked · %s — %s (+%s pts)</div>"
                % (html.escape(meta["name"]), html.escape(meta["desc"]), meta["points"]),
                unsafe_allow_html=True,
            )
def show_progress(name: str) -> None:
    participants_df, punishments_df = load_data()
    if participants_df.empty or name not in participants_df["Name"].astype(str).values:
        st.warning("Participant not found — try rejoining.")
        return
    participant = participants_df[participants_df["Name"] == name].iloc[0]
    completed = completed_list(participant["CompletedPubs"])
    progress = len(completed)
    current_pub_idx = int(participant["CurrentPub"])
    st.progress(progress / 16)
    st.markdown(
        "<div class='metric-strip'>"
        "<div class='metric-card'><div class='val'>%d/16</div><div class='lbl'>Completed</div></div>"
        "<div class='metric-card'><div class='val'>%d</div><div class='lbl'>Remaining</div></div>"
        "<div class='metric-card'><div class='val'>%d</div><div class='lbl'>Points</div></div>"
        "</div>"
        % (progress, 16 - progress, int(participant["Points"])),
        unsafe_allow_html=True,
    )
    show_achievements(participant)
    if current_pub_idx < 16:
        pub_name = PUBS_DATA["name"][current_pub_idx]
        pub_rule = PUBS_DATA["rules"][current_pub_idx]
        st.markdown(
            "<div class='pub-card'><h3>Current stop: %s</h3>"
            "<p><b>Challenge rule:</b> %s</p></div>"
            % (html.escape(pub_name), html.escape(pub_rule)),
            unsafe_allow_html=True,
        )
        if st.button("Mark Pub as Complete (+100 pts)", type="primary", use_container_width=True):
            completed.append(pub_name)
            idx = participants_df[participants_df["Name"] == name].index[0]
            participants_df.loc[idx, "CompletedPubs"] = ",".join(completed)
            participants_df.loc[idx, "CurrentPub"] = current_pub_idx + 1
            participants_df.loc[idx, "Points"] = int(participants_df.loc[idx, "Points"]) + 100
            newly = award_achievements(participants_df, idx, completed)
            save_data(participants_df, punishments_df)
            if newly:
                st.session_state["_flash_achievements"] = newly
            auto_refresh()
    else:
        st.success("Absolute legend — you've finished all 16 stops at Boombox!")
    if st.session_state.get("_flash_achievements"):
        for a in st.session_state.pop("_flash_achievements"):
            st.toast("Achievement unlocked: %s" % a)
def show_leaderboard() -> None:
    st.subheader("Live Crawl Leaderboard")
    participants_df, punishments_df = load_data()
    if not participants_df.empty:
        board = []
        for _, row in participants_df.iterrows():
            comp = completed_list(row["CompletedPubs"])
            ach = achievement_keys(row["Achievements"])
            board.append(
                {
                    "Name": row["Name"],
                    "Pubs Completed": len(comp),
                    "Points": int(row["Points"]),
                    "Achievements": len(ach),
                }
            )
        df = pd.DataFrame(board).sort_values(["Points", "Pubs Completed"], ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No crawlers yet — be the first.")
    if not punishments_df.empty:
        st.subheader("Recent Punishments Log")
        st.dataframe(
            punishments_df.tail(8).sort_values("Time", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
def show_route_list() -> None:
    with st.expander("Full 16-stop order", expanded=False):
        for i, name in enumerate(PUBS_DATA["name"], start=1):
            st.write("%d. %s" % (i, name.replace("%d. " % i, "")))
def main() -> None:
    inject_theme()
    inject_floating_elf()
    name_entry_modal()
    if not st.session_state.current_participant:
        show_route_list()
        mode = "GitHub CSV" if USE_GITHUB else "local CSV (offline demo)"
        st.caption("Persistence: " + mode)
        return
    st.markdown(
        "<div class='brand-hero' style='padding-top:0.4rem;'>"
        "<p class='brand' style='font-size:clamp(1.4rem,5vw,2rem);'>Mark's Belfast Christmas Crawl</p>"
        "<p class='tagline'>Good luck, %s!</p></div>"
        % html.escape(st.session_state.current_participant),
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.markdown("**Crawler:** `%s`" % st.session_state.current_participant)
        st.caption("GitHub CSV" if USE_GITHUB else "Local CSV mode")
        if st.button("Refresh Data", use_container_width=True):
            auto_refresh()
        if st.button("Switch crawler", use_container_width=True):
            st.session_state.current_participant = None
            auto_refresh()
    tabs = st.tabs(["Progress", "Route Map", "Wheel", "Leaderboard"])
    with tabs[0]:
        show_progress(st.session_state.current_participant)
        show_route_list()
    with tabs[1]:
        show_map()
    with tabs[2]:
        show_punishment_wheel()
    with tabs[3]:
        show_leaderboard()
if __name__ == "__main__":
    main()
