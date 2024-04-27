// package data in a JSON object
var form = document.getElementById("signup_form")
var email = document.getElementById("email_signup")
var password = document.getElementById("password")

form.addEventListener('submit', function(event) {
    event.preventDefault();
    var data_d = {'email': email.value, 'password': password.value}
    console.log('data_d', data_d)
    addCredentials(data_d);
});
function addCredentials(data_d) {
    // SEND DATA TO SERVER VIA jQuery.ajax({})
    jQuery.ajax({
        url: "/processSignup",
        data: data_d,
        type: "POST",
        dataType: "json",
        success:function(returned_data){
            console.log(returned_data['success'])
            if (returned_data['success'] == 1) {
                window.location.href = "/login";
            }
            else {
                message = document.getElementById('failed_attempts')
                message.textContent = 'Account already exists';
            }
            }
    });
}