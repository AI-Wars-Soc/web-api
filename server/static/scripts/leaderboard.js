class Leaderboard {
    static get_entry_id(index) {
        return "leaderboard-entry-" + (index + 1);
    }

    static get_leaderboard_item(index) {
        return $("#" + Leaderboard.get_entry_id(index));
    }

    static fade_in(delta, duration) {
        let index = 0;
        let item = Leaderboard.get_leaderboard_item(index);
        while(item.length !== 0) {
            const delay = delta * index;
            item.hide();
            window.setTimeout(Leaderboard.fade_in_one, delay, item, duration);

            index++;
            item = this.get_leaderboard_item(index);
        }
    }

    static fade_in_one(entry, duration) {
        entry.show("slide", {direction: "right"}, duration);
    }

    static fade_out_and_reload(delta, duration) {
        let index = 0;
        let item = this.get_leaderboard_item(index);
        while(item.length !== 0) {
            const delay = delta * index;
            window.setTimeout(Leaderboard.fade_out_one, delay, item, duration);

            index++;
            item = this.get_leaderboard_item(index);
        }

        const delay = delta * index + duration;
        window.setTimeout(() => window.location.reload(), delay);
    }

    static fade_out_one(entry, duration) {
        entry.hide("slide", {direction: "left"}, duration);
    }
}

{
    const leaderboard_duration = 1000;
    const leaderboard_delta = 250;
    const leaderboard_reload_time = 5 * 60 * 1000;

    Leaderboard.fade_in(leaderboard_delta, leaderboard_duration);
    window.setInterval(Leaderboard.fade_out_and_reload, leaderboard_reload_time, leaderboard_delta, leaderboard_duration);
}
