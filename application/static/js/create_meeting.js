$('#create_meeting').on('click', function(event) {
    var meeting_name = $('#meeting_name').val();
    var your_email = $('#your_email').val();
    var daterange = $('#daterange').val();
    var meeting_begin = $('#meeting_begin').val();
    var meeting_end = $('meeting_end').val();
    var group_emails = $('group_emails').val();
    console.log("daterange" + daterange);
    console.log("group_emails" + group_emails);
});