function _gcd_two(a, b)
{
    if (b === 0)
        return a;
    return _gcd_two(b, a % b);
}

function gcd(...arr)
{
    let ans = arr[0];

    for (let i = 1; i < arr.length; i++) {
        ans = _gcd_two(arr[i], ans);
    }

    return ans;
}

function convert_date(unix) {
    const date = new Date(unix * 1000);

    const day = date.getDay();
    const month = date.getMonth();
    const hours = date.getHours();
    const minutes = "0" + date.getMinutes();

    return day + "/" + month + " " + hours + ':' + minutes.substr(-2);
}

class Leaderboard {
    constructor(duration = 1000, delta = 250) {
        this.duration = duration;
        this.delta = delta;

        this.seenBefore = localStorage.seenLeaderboard === '1';
        localStorage.seenLeaderboard = '1';
    }

    static reset() {
        localStorage.seenLeaderboard = '0';
    }

    static get_entry_id(index) {
        return "leaderboard-entry-" + (index + 1);
    }

    static get_leaderboard_item(index) {
        return $("#" + Leaderboard.get_entry_id(index));
    }

    fade_in(f_after) {
        if (this.seenBefore) {
            f_after();
            return;
        }

        let index = 0;
        let item = Leaderboard.get_leaderboard_item(index);
        while(item.length !== 0) {
            const delay = this.delta * index;
            item.hide();
            window.setTimeout(Leaderboard.fade_in_one, delay, item, this.duration);

            index++;
            item = Leaderboard.get_leaderboard_item(index);
        }
        window.setTimeout(f_after, this.delta * index + this.duration);
    }

    static fade_in_one(entry, duration) {
        entry.show("slide", {direction: "right"}, duration);
    }


    static get_graph_data(users, deltas, initial_score) {
        // Get all sampled time steps
        let timestamp_set = new Set();
        for (let i = 0; i < deltas.length; i++) {
            const delta = deltas[i];
            timestamp_set.add(delta.time);
        }
        const referenced_timestamps = Array.from(timestamp_set);
        const timestep = gcd(...referenced_timestamps);
        const timestamp_min = Math.min(...referenced_timestamps) - timestep;
        const timestamp_max = Math.max(...referenced_timestamps);

        // Fill in blanks
        let timestamps = [];
        let labels = [];
        let timestamp = timestamp_min;
        let timestamp_i = 0;
        while (timestamp <= timestamp_max) {
            timestamps.push(timestamp);
            labels.push(convert_date(timestamp));
            timestamp += timestep;
            timestamp_i += 1;
        }

        // Make user data
        const user_id_points = new Map();
        const user_ids = Array.from(Object.keys(users));
        for (let i = 0; i < user_ids.length; i++) {
            const user_id = user_ids[i];
            const points = new Array(timestamps.length);
            points.fill(NaN);
            user_id_points.set(user_id, points);
        }

        // Populate user data
        for (let i = 0; i < deltas.length; i++) {
            const delta = deltas[i];
            const timestamp_i = Math.round((delta.time - timestamp_min) / timestep);
            const points = user_id_points.get("" + delta.user_id);

            if (timestamp_i > 0 && isNaN(points[timestamp_i - 1])) {
                points[timestamp_i - 1] = initial_score;
            }
            for (let j = timestamp_i; j < points.length; j++){
                if (isNaN(points[j])) {
                    points[j] = initial_score;
                }
                points[j] += delta.delta;
            }
        }

        // Make full data array
        let datasets = [];
        for (let i = 0; i < user_ids.length; i++) {
            const user_id = user_ids[i];
            const user = users[user_id]

            let color = "#676767";
            if (user.is_you === true) {
                color = "#2D7DD2";
            } else if (user.is_bot === true) {
                color = "#90001C";
            }

            datasets.push({
                    label: user.display_name,
                    data: user_id_points.get(user_id),
                    fill: false,
                    radius: 1,
                    hitRadius: 3,
                    hoverRadius: 6,
                    borderColor: color,
                    cubicInterpolationMode: 'monotone',
                    tension: 0.4
                });
        }
        return {
            labels: labels,
            datasets: datasets
        };
    }

    static make_graph_dom() {
        $("#overTimeChartContainer").append($("<canvas />", {id: "overTimeChart"}).hide());
    }

    make_graph() {
        // Make graph object
        Leaderboard.make_graph_dom();
        const ctx = document.getElementById('overTimeChart').getContext('2d');
        const config = {
            type: 'line',
            data: [],
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: false,
                        text: 'Leaderboard'
                    },
                },
                interaction: {
                intersect: false,
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Score'
                        },
                    }
                }
            },
        };
        this.chart = new Chart(ctx, config);

        const chart_jquery = $("#overTimeChart");
        if (this.seenBefore) {
            chart_jquery.show();
        } else {
            chart_jquery.show("blind");
        }

        const leaderboard = this;
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/get_leaderboard_over_time');
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onload = function () {
            const response = JSON.parse(xhr.responseText);
            const json_data = response.data;

            leaderboard.chart.data = Leaderboard.get_graph_data(json_data.users, json_data.deltas, json_data.initial_score);
            leaderboard.chart.update();
        };
        xhr.send();
    }
}

leaderboard = new Leaderboard(1000, 250);

leaderboard.fade_in(() => leaderboard.make_graph());
