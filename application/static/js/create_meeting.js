$('#create_meeting').on('click', function(event) {
    var meeting_name = $('#meeting_name').val();
    var your_email = $('#your_email').val();
    var daterange = $('#daterange').val();
    var meeting_begin = $('#meeting_begin').val();
    var meeting_end = $('#meeting_end').val();
    var group_emails = $('#group_emails').tokenfield('getTokensList');
    var emails = group_emails.split(",").map(function(item) {
            return item.trim();
        });
    if (meeting_name && your_email && daterange && meeting_begin && meeting_end
    && emails) {
        post_json = {
        meeting_name: meeting_name,
        your_email: your_email,
        daterange: daterange,
        meeting_begin: meeting_begin,
        meeting_end: meeting_end,
        group_emails: emails}
        $.post('/initialize_meeting', post_json, function(data) {
            window.location = data.result;
        });
    } else {
        console.log("invalid");
    }
});