async function loadEmployees(){

    const response = await fetch("/employees");

    const employees = await response.json();

    let html = "";

    employees.forEach(emp=>{

        html += `
        <div class="card">

            <h3>

                ${emp.online
                    ? '<span class="online">🟢</span>'
                    : '<span class="offline">🔴</span>'}

                ${emp.name}

            </h3>

            <img src="${emp.image}">

        </div>
        `;

    });

    document.getElementById("grid").innerHTML = html;

}

loadEmployees();

setInterval(loadEmployees,1000);