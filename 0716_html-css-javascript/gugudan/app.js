//** 콘솔에 출력. 당연히..

// for (let i = 2; i <= 9; i++) {
//     console.log(`=== ${i}단 ===`);

//     for (let j = 1; j <= 9; j++) {
//         console.log(`${i} x ${j} = ${i * j}`);
//     }

//     console.log();
// }


// ** 브라우저에 출력

let text = "";

for (let i = 2; i <= 9; i++) {
    text += `<h2>${i}단</h2>`;

    for (let j = 1; j <= 9; j++) {
        text += `${i} × ${j} = ${i * j}<br>`;
    }
}

document.getElementById("result").innerHTML = text;