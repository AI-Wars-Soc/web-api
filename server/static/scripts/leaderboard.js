import React from 'react';

class Leaderboard extends React.Component {
    render() {
        return (
            <h1>Hello, World!</h1>
        );
    }
}

/*let current_leaderboard = [];

function get_submission_id(i, l) {
    return l[i].submission.submission_id;
}

function get_user_name(i, l) {
    return l[i].user.display_name;
}

function get_score(i, l) {
    return l[i].score;
}

function get_and_update_leaderboard() {
    // Get
    $.getJSON('/api/get_leaderboard', function (data) {
        update_leaderboard(data);
    });
}

function get_entry_id(index) {
    return "leaderboard-entry-" + index;
}

function create_blank_entry(index) {
    const entry_id = get_entry_id(index);

    // JSX is so fucking cool
    return <div id={entry_id} style="display: none ;">
        <div className="d-flex flex-row w-100 m-1 m-md-2">
            <div className="w-25 leaderboard-position">
            </div>
            <div className="w-50 leaderboard-name">
            </div>
            <div className="w-25 leaderboard-score">
            </div>
        </div>
    </div>;
}

function get_leaderboard_item(index) {
    return $(get_entry_id(index));
}

function populate_leaderboard_item(entry, data) {

}

function update_leaderboard(new_leaderboard) {
    const duration = 1000;
    const delta = 250;

    // Remove excess
    for (let i = new_leaderboard.length; i < current_leaderboard.length; i++) {
        get_leaderboard_item(i).remove();
    }

    // Add new blanks
    const leaderboard_div = $("#leaderboard");
    for (let i = current_leaderboard.length; i < new_leaderboard.length; i++) {
        leaderboard_div.append(create_blank_entry(i));
    }

    // Fade all out
    for (let i = 0; i < new_leaderboard.length; i++) {
        const delay = delta * i;
        const entry = get_leaderboard_item(i);
        const data = new_leaderboard[i];
        window.setTimeout(hide_populate_and_show, delay, entry, data, duration);
    }

    current_leaderboard = new_leaderboard;
}

function hide_populate_and_show(entry, data, duration) {
    entry.hide("slide", {direction: "left"}, duration, function () {
        populate_leaderboard_item(entry, data);
        entry.show("slide", {direction: "right"}, duration);
    });
}

get_and_update_leaderboard();
window.setInterval(get_and_update_leaderboard, 5 * 60 * 1000); */

export default Leaderboard;