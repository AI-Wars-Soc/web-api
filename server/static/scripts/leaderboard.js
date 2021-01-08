class Leaderboard {
    constructor() {
        this.current_leaderboard = [];
    }

    static get_and_update_leaderboard(leaderboard) {
        // Get
        $.getJSON('/api/get_leaderboard', function (data) {
            leaderboard.update_leaderboard(data);
        });
    }

    static get_entry_id(index) {
        return "leaderboard-entry-" + index;
    }

    static create_blank_entry(index) {
        const entry_id = Leaderboard.get_entry_id(index);

        return $("<div />", {id: entry_id,})
            .append($("<div />", {"class": "d-flex flex-row w-100 m-1 m-md-2"})
                .append($("<div />", {"class": "w-25 leaderboard-position"}))
                .append($("<div />", {"class": "w-50 leaderboard-name"}))
                .append($("<div />", {"class": "w-25 leaderboard-score"}))
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

    static get_pos(last_pos, data) {
        if (data.score === last_pos.score) {
            return {pos: last_pos.pos, score: data.score, same: true};
        }
        return {pos: last_pos.pos + 1, score: data.score, same: false};
    }

    update_leaderboard(new_leaderboard) {
        const duration = 1000;
        const delta = 250;

        // Remove excess
        for (let i = new_leaderboard.length; i < this.current_leaderboard.length; i++) {
            const delay = delta * i;
            const entry = Leaderboard.get_leaderboard_item(i);
            window.setTimeout(Leaderboard.hide_and_execute, delay, entry, duration, function () {
                Leaderboard.delete(entry);
            });
        }

        // Add new blanks
        const leaderboard_div = $("#leaderboard");
        for (let i = this.current_leaderboard.length; i < new_leaderboard.length; i++) {
            leaderboard_div.append(Leaderboard.create_blank_entry(i));
        }

        // Fade all out
        let last_pos = {pos: 0, score: Infinity, same: false};
        for (let i = 0; i < new_leaderboard.length; i++) {
            const delay = delta * i;
            const entry = Leaderboard.get_leaderboard_item(i);
            const data = new_leaderboard[i];
            const pos = Leaderboard.get_pos(last_pos, data);
            const pos_str = (pos.same ? "=" : "") + pos.pos;
            window.setTimeout(Leaderboard.hide_and_execute, delay, entry, duration, function () {
                Leaderboard.populate_and_show(entry, data, duration, pos_str);
            });
            last_pos = pos;
        }

        this.current_leaderboard = new_leaderboard;
    }

    static hide_and_execute(entry, duration, f) {
        entry.hide("slide", {direction: "left"}, duration, function () {
            f();
        });
    }

    static delete(entry) {
        $(entry).remove();
    }

    static populate_and_show(entry, data, duration, position) {
        Leaderboard.populate_leaderboard_item(entry, data, position);
        entry.show("slide", {direction: "right"}, duration);
    }
}

const leaderboard = new Leaderboard();
Leaderboard.get_and_update_leaderboard(leaderboard);
window.setInterval(Leaderboard.get_and_update_leaderboard, 5 * 60 * 1000, leaderboard);