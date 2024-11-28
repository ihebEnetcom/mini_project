document.getElementById('appointment-form').addEventListener('submit',(event)=>{
 const name=document.getElementById("name").value;
 const date=document.getElementById("date").value;
 const time=document.getElementById("time").value;
 console.log(!name||!date||!time);
 if(!name||!date||!time){
    alert('veuillez remplir tous les champs.');
    event.preventDefault();
 }

});