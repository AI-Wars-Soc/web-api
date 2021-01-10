$('#submission-form').submit(function(e){
    e.preventDefault();
    const url = $("#repo").text();
    $.post("/api/add_submission", JSON.stringify({url: url}), function(receivedData){
        console.log(receivedData);
    });
});