const tg = window.Telegram ? window.Telegram.WebApp : null;
const initData = tg?.initData || "";

const state = {
  board: Array(9).fill(null),
  player: "X",
  bot: "O",
  finished: false,
  mode: "easy",
  thinking: false,
};

const winningLines = [
  [0, 1, 2],
  [3, 4, 5],
  [6, 7, 8],
  [0, 3, 6],
  [1, 4, 7],
  [2, 5, 8],
  [0, 4, 8],
  [2, 4, 6],
];

const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const resultPanel = document.getElementById("result-panel");
const resultMessage = document.getElementById("result-message");
const promoCard = document.getElementById("promo-card");
const promoCodeEl = document.getElementById("promo-code");
const copyBtn = document.getElementById("copy-btn");
const copyHint = document.getElementById("copy-hint");
const restartBtn = document.getElementById("restart-btn");
const againBtn = document.getElementById("again-btn");
const gamePanel = document.getElementById("game-panel");
const warningEl = document.getElementById("telegram-warning");
const modeToggle = document.getElementById("mode-toggle");

function applyTheme() {
  if (!tg || !tg.themeParams) return;
  const p = tg.themeParams;
  const map = {
    "--card": p.secondary_bg_color,
    "--card-muted": p.secondary_bg_color,
    "--text": p.text_color,
    "--muted": p.hint_color,
    "--accent": p.accent_text_color,
    "--accent-strong": p.button_color,
    "--border": p.section_separator_color,
  };
  Object.entries(map).forEach(([key, value]) => {
    if (value) document.documentElement.style.setProperty(key, value);
  });
}

function initTelegram() {
  if (!tg) {
    warningEl.hidden = false;
    gamePanel.hidden = true;
    return;
  }

  tg.ready();
  tg.expand();
  applyTheme();
}

function renderBoard() {
  boardEl.querySelectorAll(".cell").forEach((cell) => {
    const idx = Number(cell.dataset.index);
    const value = state.board[idx];
    cell.textContent = value ?? "";
    cell.classList.toggle("cell--x", value === "X");
    cell.classList.toggle("cell--o", value === "O");
    cell.disabled = Boolean(value) || state.finished || state.thinking;
  });
}

function availableMoves(board) {
  return board
    .map((value, idx) => (value === null ? idx : null))
    .filter((idx) => idx !== null);
}

function evaluate(board) {
  for (const [a, b, c] of winningLines) {
    if (board[a] && board[a] === board[b] && board[a] === board[c]) {
      return board[a] === state.bot ? 10 : -10;
    }
  }
  return 0;
}

function minimax(board, depth, isMaximizing) {
  const score = evaluate(board);
  if (score === 10) return score - depth;
  if (score === -10) return score + depth;

  const moves = availableMoves(board);
  if (moves.length === 0) return 0;

  if (isMaximizing) {
    let best = -Infinity;
    for (const move of moves) {
      board[move] = state.bot;
      best = Math.max(best, minimax(board, depth + 1, false));
      board[move] = null;
    }
    return best;
  }

  let best = Infinity;
  for (const move of moves) {
    board[move] = state.player;
    best = Math.min(best, minimax(board, depth + 1, true));
    board[move] = null;
  }
  return best;
}

function pickBotMoveSmart(board) {
  const moves = availableMoves(board);
  if (moves.length === 0) return null;

  if (Math.random() < 0.18) {
    return moves[Math.floor(Math.random() * moves.length)];
  }

  let bestVal = -Infinity;
  let bestMove = moves[0];
  for (const move of moves) {
    board[move] = state.bot;
    const moveVal = minimax(board, 0, false);
    board[move] = null;
    if (moveVal > bestVal) {
      bestMove = move;
      bestVal = moveVal;
    }
  }
  return bestMove;
}

function pickBotMoveEasy(board) {
  const moves = availableMoves(board);
  if (moves.length === 0) return null;
  const priority = [4, 0, 2, 6, 8, 1, 3, 5, 7];
  const preferred = priority.find((idx) => moves.includes(idx));
  if (preferred !== undefined && Math.random() > 0.3) return preferred;
  return moves[Math.floor(Math.random() * moves.length)];
}

function getWinner(board) {
  for (const [a, b, c] of winningLines) {
    if (board[a] && board[a] === board[b] && board[a] === board[c]) {
      return board[a];
    }
  }
  return null;
}

function isDraw(board) {
  return availableMoves(board).length === 0 && !getWinner(board);
}

function setStatus(text) {
  statusEl.textContent = text;
}

async function sendResult(result, promoHandler) {
  if (!initData) {
    setStatus("Откройте игру из Telegram, чтобы отправить результат.");
    return;
  }
  if (!tg) return;
  try {
    const response = await fetch("/api/result", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ result, init_data: initData, initData }),
    });
    if (!response.ok) throw new Error("Сервер ответил ошибкой");
    const data = await response.json();
    const promo = data.promo_code ?? data.promoCode;
    if (promoHandler) promoHandler(promo);
  } catch (err) {
    setStatus("Не удалось отправить результат, попробуйте ещё раз.");
    console.error(err);
  }
}

function showResult(type, promoCode) {
  resultPanel.hidden = false;
  promoCard.hidden = true;
  copyHint.hidden = true;

  if (type === "win") {
    resultMessage.textContent = promoCode
      ? "Промокод отправили вам в Telegram, загляните в чат."
      : "Промокод отправили вам в Telegram, загляните в чат.";
    promoCard.hidden = true;
  } else if (type === "lose") {
    resultMessage.textContent = "В этот раз выиграл компьютер. Хотите реванш?";
  } else {
    resultMessage.textContent = "Ничья. Попробуем ещё раз?";
  }
}

function finishGame(outcome) {
  state.finished = true;
  setStatus(outcome === "win" ? "Вы победили 🎉" : outcome === "lose" ? "Компьютер победил" : "Ничья");
  if (outcome === "win") {
    showResult("win");
    sendResult("win", (promo) => showResult("win", promo));
  } else if (outcome === "lose") {
    sendResult("lose");
    showResult("lose");
  } else {
    sendResult("draw");
    showResult("draw");
  }
}

function botTurn() {
  if (state.finished) return;
  state.thinking = true;
  renderBoard();
  setStatus("Компьютер думает...");

  setTimeout(() => {
    const move =
      state.mode === "smart"
        ? pickBotMoveSmart([...state.board])
        : pickBotMoveEasy([...state.board]);

    if (move !== null) {
      state.board[move] = state.bot;
      renderBoard();
    }

    const winner = getWinner(state.board);
    if (winner === state.bot) {
      finishGame("lose");
    } else if (isDraw(state.board)) {
      finishGame("draw");
    } else {
      state.thinking = false;
      setStatus("Ваш ход");
      renderBoard();
    }
  }, 450);
}

function handlePlayerMove(index) {
  if (state.finished || state.thinking) return;
  if (state.board[index]) return;

  state.board[index] = state.player;
  renderBoard();

  const winner = getWinner(state.board);
  if (winner === state.player) {
    finishGame("win");
    return;
  }

  if (isDraw(state.board)) {
    finishGame("draw");
    return;
  }

  botTurn();
}

function resetGame() {
  state.board = Array(9).fill(null);
  state.finished = false;
  state.thinking = false;
  setStatus("Ваш ход");
  resultPanel.hidden = true;
  renderBoard();
}

boardEl.addEventListener("click", (event) => {
  const btn = event.target.closest(".cell");
  if (!btn) return;
  handlePlayerMove(Number(btn.dataset.index));
});

modeToggle.addEventListener("click", (event) => {
  const btn = event.target.closest(".mode-toggle__btn");
  if (!btn) return;
  const mode = btn.dataset.mode;
  if (mode && state.mode !== mode) {
    state.mode = mode;
    modeToggle.querySelectorAll(".mode-toggle__btn").forEach((b) => b.classList.remove("is-active"));
    btn.classList.add("is-active");
    resetGame();
  }
});

restartBtn.addEventListener("click", resetGame);
againBtn.addEventListener("click", resetGame);

copyBtn.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(promoCodeEl.textContent);
    copyHint.hidden = false;
    setTimeout(() => (copyHint.hidden = true), 1500);
  } catch (err) {
    console.error("Не удалось скопировать", err);
  }
});

initTelegram();
renderBoard();
