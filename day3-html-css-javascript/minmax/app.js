// const input = document.getElementById("numbers");
// const button = document.getElementById("findBtn");
// const result = document.getElementById("result");

// button.addEventListener("click", () => {
//     const numbers = input.value
//         .split(",")
//         .map(num => Number(num.trim()));

//     const min = Math.min(...numbers);
//     const max = Math.max(...numbers);

//     result.innerHTML = `
//         <p><strong>입력값:</strong> [${numbers.join(", ")}]</p>
//         <p><strong>최소값:</strong> ${min}</p>
//         <p><strong>최대값:</strong> ${max}</p>
//     `;
// });

const input = document.getElementById("numbers");

document.querySelector("button").addEventListener("click", () => {
    const numbers = input.value
        .split(",")
        .map(num => Number(num.trim()));

    const min = Math.min(...numbers);
    const max = Math.max(...numbers);

    console.clear();
    console.log("입력 배열:", numbers);
    console.log(`최소값: ${min}, 최대값: ${max}`);
});