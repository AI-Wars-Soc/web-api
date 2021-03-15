$('#submission-form').submit(function(e){
    e.preventDefault();
    const url = $("#repo").val();
    $.post(
        {
            url: "/api/add_submission",
            data: JSON.stringify({url: url}),
            contentType: 'application/json',
            success: function(receivedData){
                console.log(receivedData);
            }
        }
    );
});