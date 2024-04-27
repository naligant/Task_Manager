
function addMember() {
    const divEle = document.getElementById("input_email");
    const space = document.createElement("br")
    const wrapper = document.createElement("div");
    const inputMember = document.createElement("input");
    inputMember.setAttribute("type", "text");
    inputMember.setAttribute("placeholder", "Enter Member Email");
    inputMember.classList.add("new_element");
    wrapper.appendChild(space);
    wrapper.appendChild(inputMember);
    wrapper.appendChild(space);
    divEle.appendChild(wrapper);
}


function get_values() {
    const inputs = document.querySelectorAll(".new_element");
    const values = [];
    inputs.forEach(input =>{
        values.push(input.value);
    });
    
    return values
}

function Submission(){
    var name = document.getElementById("project_name")
    var emails = get_values()
    var data_d = {'name': name.value, 'emails': emails}
    console.log('data_d', data_d)
    addProject(data_d);

}
// function addProject(data_d){
//     jQuery.ajax({
//         url: "/processboard",
//         data: data_d,
//         type: "POST",
//         dataType: "json",
//         success:function(returned_data){
//             console.log(data_d)
//             console.log(returned_data['success'])
//             // if (returned_data['success'] == 1) {

//             // }
//         }
//     });
// }

function addProject(data_d) {
    // SEND DATA TO SERVER VIA jQuery.ajax({})
    jQuery.ajax({
        url: "/processboard",
        data: data_d,
        type: "POST",
        dataType: "json",
        success:function(returned_data){
            console.log(returned_data['success'])
            // if (returned_data['success'] == 1) {
            //     window.location.href = "/board_type";
            // }
            // else {
            //     message = document.getElementById('failed_attempts')
            //     message.textContent = 'Authentication failure';
            // }
            //   returned_data = JSON.parse(returned_data);
            //   window.location.href = "/home";
            }
    });
}