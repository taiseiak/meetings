$.get("/get_free_times", function(data) {
    $('#users').html("");
    $('#open_times').html("");
    var free_times = data.result.free_times;
    var users = data.result.users;
    var users_length = users.length;
    for (i=0; i < users_length; i ++) {
        var user = users[i];
        var email = user.email;
        var responded = user.responded;
        if (responded == true) {
            var user_string = "<div class='text-center'><div class='alert alert-info'><strong>" + email +
               "</strong> has responded</div></div>";
             $('#users').append(user_string);
        } else {
            var user_string = "<div class='text-center'><div class='alert alert-warning'><strong>" + email +
               "</strong> has not yet responded</div></div>";
             $('#users').append(user_string);
        }
    }
    var free_length = free_times.length;
    for (i = 0; i < free_length; i ++) {
         var free_string = "<div class='text-center'><div class='alert alert-success'>Free Time<br> Start time: <strong>" + moment(free_times[i].start).format('dddd, MMMM Do YYYY, h:mm') +
           "</strong><br> End time: <strong>" + moment(free_times[i].end).format('dddd, MMMM Do YYYY, h:mm') + "</strong></div></div>";
         $('#open_times').append(free_string);
    }
});

