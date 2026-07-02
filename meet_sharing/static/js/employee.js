let stream = null;

let video = document.createElement("video");

let canvas = document.createElement("canvas");

let ctx = canvas.getContext("2d");

const btn = document.getElementById("shareBtn");

const status = document.getElementById("status");

btn.onclick = async function(){

    const name = document.getElementById("name").value.trim();

    if(name===""){

        alert("Enter your name");

        return;

    }

    try{

        stream = await navigator.mediaDevices.getDisplayMedia({

            video:true,

            audio:false

        });

        video.srcObject = stream;

        await video.play();

        status.innerHTML="Sharing...";

        setInterval(function(){

            capture(name);

        },1000);

    }

    catch(err){

        alert(err);

    }

}

function capture(name){

    canvas.width=video.videoWidth;

    canvas.height=video.videoHeight;

    ctx.drawImage(video,0,0);

    let image=canvas.toDataURL("image/jpeg",0.6);

    fetch("/upload",{

        method:"POST",

        headers:{

            "Content-Type":"application/json"

        },

        body:JSON.stringify({

            name:name,

            image:image

        })

    });

}