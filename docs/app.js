const commands = {
  unix: "curl -fsSL https://raw.githubusercontent.com/claudneysessa/ctx404/main/install.sh | sh",
  windows: "irm https://raw.githubusercontent.com/claudneysessa/ctx404/main/install.ps1 | iex"
};

const command = document.querySelector("#install-command");
const brandCommand = document.querySelector("#brand-command");
let language = "en";

function typeBrandCommand() {
  const text = "ctx404";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    brandCommand.textContent = text;
    return;
  }

  let index = 0;
  const typeNext = () => {
    brandCommand.textContent = text.slice(0, index);
    index += 1;
    if (index <= text.length) {
      window.setTimeout(typeNext, 72 + Math.random() * 65);
    }
  };

  window.setTimeout(typeNext, 380);
}

function setLanguage(next) {
  language = next;
  document.documentElement.lang = next === "pt" ? "pt-BR" : "en";
  document.querySelectorAll("[data-en]").forEach((item) => {
    item.innerHTML = item.dataset[next];
  });
  document.querySelectorAll(".language").forEach((button) => {
    button.classList.toggle("active", button.dataset.lang === next);
  });
}

document.querySelectorAll(".language").forEach((button) => {
  button.addEventListener("click", () => setLanguage(button.dataset.lang));
});

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("active"));
    tab.classList.add("active");
    command.textContent = commands[tab.dataset.platform];
  });
});

document.querySelector(".copy").addEventListener("click", async (event) => {
  await navigator.clipboard.writeText(command.textContent);
  event.currentTarget.textContent = language === "pt" ? "copiado!" : "copied!";
  setTimeout(() => {
    event.currentTarget.textContent = language === "pt" ? "copiar" : "copy";
  }, 1400);
});

setLanguage("en");
typeBrandCommand();
