class Leaderboard {
    constructor() {
        this.current_leaderboard = [];
    }

    get_and_update_leaderboard() {
        // Get
        const l = this;
        $.getJSON('/api/get_leaderboard', function (data) {
            l.update_leaderboard(data);
        });
    }

    static get_entry_id(index) {
        return "leaderboard-entry-" + index;
    }

    static create_blank_entry(index) {
        const entry_id = Leaderboard.get_entry_id(index);

        return $("<div />", { id: entry_id, })
            .append($("<div />", { "class": "d-flex flex-row w-100 m-1 m-md-2" })
                .append($("<div />", { "class": "w-25 leaderboard-position" }))
                .append($("<div />", { "class": "w-50 leaderboard-name" }))
                .append($("<div />", { "class": "w-25 leaderboard-score" }))
        ).hide();
    }

    static get_leaderboard_item(index) {
        return $("#" + Leaderboard.get_entry_id(index));
    }

    static populate_leaderboard_item(entry, data, position) {
        entry = $(entry);
        entry.find(".leaderboard-position").text(position);
        entry.find(".leaderboard-name").text(data.user.display_name);
        entry.find(".leaderboard-score").text(data.score);
    }

    update_leaderboard(new_leaderboard) {
        const duration = 1000;
        const delta = 250;

        // Remove excess
        for (let i = new_leaderboard.length; i < this.current_leaderboard.length; i++) {
            Leaderboard.get_leaderboard_item(i).remove();
        }

        // Add new blanks
        const leaderboard_div = $("#leaderboard");
        for (let i = this.current_leaderboard.length; i < new_leaderboard.length; i++) {
            leaderboard_div.append(Leaderboard.create_blank_entry(i));
        }

        // Fade all out
        for (let i = 0; i < new_leaderboard.length; i++) {
            const delay = delta * i;
            const entry = Leaderboard.get_leaderboard_item(i);
            const data = new_leaderboard[i];
            window.setTimeout(Leaderboard.hide_populate_and_show, delay, entry, data, duration);
        }

        this.current_leaderboard = new_leaderboard;
    }

    static hide_populate_and_show(entry, data, duration) {
        entry.hide("slide", {direction: "left"}, duration, function () {
            Leaderboard.populate_leaderboard_item(entry, data, "1");
            entry.show("slide", {direction: "right"}, duration);
        });
    }
}

const leaderboard = new Leaderboard();
leaderboard.get_and_update_leaderboard();
window.setInterval(leaderboard.get_and_update_leaderboard, 5 * 60 * 1000);