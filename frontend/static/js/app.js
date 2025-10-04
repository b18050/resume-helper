const form = document.getElementById("job-form");
const submitButton = form.querySelector("button[type='submit']");
const buttonText = document.getElementById("button-text");
const buttonLoader = document.getElementById("button-loader");
const statusCard = document.getElementById("status-card");
const warningCard = document.getElementById("warning-card");
const keywordsCard = document.getElementById("keywords-card");
const extractedCard = document.getElementById("extracted-card");
const blockCard = document.getElementById("block-card");
const downloadWrapper = document.getElementById("download-wrapper");
const downloadButton = document.getElementById("download-button");
const downloadPdfButton = document.getElementById("download-pdf-button");
const pdfButtonText = document.getElementById("pdf-button-text");
const pdfButtonLoader = document.getElementById("pdf-button-loader");
const resumeInput = document.getElementById("resume");
const resumeSourceRadios = document.querySelectorAll("input[name='resume_source']");

let latestResumeContent = "";
let currentCompanyName = "";

const setLoading = (isLoading) => {
  if (isLoading) {
    buttonText.textContent = "Generating...";
    buttonLoader.classList.remove("hidden");
    submitButton.setAttribute("disabled", "true");
  } else {
    buttonText.textContent = "Generate tailored resume";
    buttonLoader.classList.add("hidden");
    submitButton.removeAttribute("disabled");
  }
};

const resetCard = (card) => {
  card.classList.add("hidden");
  card.innerHTML = "";
};

const resetResults = () => {
  // Reset individual cards
  resetCard(statusCard);
  resetCard(warningCard);
  
  // Reset collapsible sections
  const keywordsDetails = document.getElementById("keywords-details");
  const latexDetails = document.getElementById("latex-details");
  
  keywordsDetails.classList.add("hidden");
  latexDetails.classList.add("hidden");
  
  // Clear content but don't hide the inner cards
  extractedCard.innerHTML = "";
  keywordsCard.innerHTML = "";
  blockCard.innerHTML = "";
  
  downloadWrapper.classList.add("hidden");
  latestResumeContent = "";
};

const updateResumeInputState = () => {
  const selected = document.querySelector("input[name='resume_source']:checked");
  const useDefault = selected && selected.value === "default";
  const uploadSection = document.getElementById("upload-section");

  if (useDefault) {
    resumeInput.value = "";
    resumeInput.removeAttribute("required");
    if (uploadSection) uploadSection.classList.add("hidden");
  } else {
    resumeInput.setAttribute("required", "true");
    if (uploadSection) uploadSection.classList.remove("hidden");
  }
};

resumeSourceRadios.forEach((radio) => {
  radio.addEventListener("change", updateResumeInputState);
});

updateResumeInputState();

const renderStatus = (summary, scraped, outputDir) => {
  statusCard.classList.remove("hidden");
  statusCard.innerHTML = `
    <h3 class="text-base font-semibold text-white/90">Resume updated successfully</h3>
    <p class="mt-2 text-sm text-white/70">${summary}</p>
    <p class="mt-3 text-xs text-white/40">Source: ${scraped ? "scraped from URL" : "manual description"}</p>
    ${outputDir ? `<p class="mt-2 text-xs text-green-400/80">✓ Saved to: ${outputDir}/Chandan_Prakash_Software.*</p>` : ""}
  `;
};

const renderWarnings = (warnings) => {
  if (!warnings.length) {
    resetCard(warningCard);
    return;
  }
  const list = warnings.map((warning) => `<li class="mb-2">${warning}</li>`).join("");
  warningCard.classList.remove("hidden");
  warningCard.innerHTML = `
    <h3 class="text-base font-semibold text-white/80">Heads up</h3>
    <ul class="mt-2 text-sm text-white/60 leading-relaxed">${list}</ul>
  `;
};

const renderExtractedKeywords = (allCandidates, missing, aiKeywords, aiEnabled) => {
  const keywordsDetails = document.getElementById("keywords-details");
  
  if (!allCandidates.length) {
    keywordsDetails.classList.add("hidden");
    return;
  }

  const missingSet = new Set((missing || []).map((keyword) => keyword.toLowerCase()));

  // Show all keywords, not just first 15
  const keywordChips = allCandidates
    .map((keyword) => {
      const isMissing = missingSet.has(keyword.toLowerCase());
      const statusClass = isMissing ? "keyword-tag--missing" : "keyword-tag--covered";
      return `<span class="keyword-tag ${statusClass}">${keyword}</span>`;
    })
    .join(" ");

  keywordsDetails.classList.remove("hidden");
  keywordsDetails.open = false; // Keep collapsed by default
  extractedCard.innerHTML = `
    <div>
      <p class="text-sm font-semibold text-white/80 mb-2">All extracted keywords (${allCandidates.length}):</p>
      <div class="flex flex-wrap gap-2">${keywordChips}</div>
      <p class="text-xs text-white/40 mt-3">
        <span class="text-green-400">Green</span> = already in resume • 
        <span class="text-red-400">Red</span> = will be added as hidden keywords
      </p>
    </div>
  `;
};

const renderKeywords = (missing, allCandidates) => {
  if (!missing.length) {
    keywordsCard.innerHTML = `
      <div class="mt-4 pt-4 border-t border-white/10">
        <p class="text-sm text-green-400">✓ Resume already covers all keywords - no changes needed!</p>
      </div>
    `;
    return;
  }

  // Show all missing keywords
  const missingTags = missing
    .map((keyword) => `<span class="keyword-tag keyword-tag--missing">${keyword}</span>`)
    .join(" ");

  keywordsCard.innerHTML = `
    <div class="mt-4 pt-4 border-t border-white/10">
      <p class="text-sm font-semibold text-white/80 mb-2">Hidden keywords to inject (${missing.length}):</p>
      <div class="flex flex-wrap gap-2">${missingTags}</div>
      <p class="text-xs text-white/40 mt-3">These will be added as invisible white text in your PDF</p>
    </div>
  `;
};

const renderWhiteBlock = (block) => {
  const latexDetails = document.getElementById("latex-details");
  
  if (!block) {
    latexDetails.classList.add("hidden");
    return;
  }
  
  const safeBlock = block.replace(/</g, "&lt;").replace(/>/g, "&gt;");
  latexDetails.classList.remove("hidden");
  latexDetails.open = false; // Keep collapsed by default
  blockCard.innerHTML = `<pre class="code-block text-xs">${safeBlock}</pre>`;
};

const buildSummary = (missingCount, candidateCount, aiEnabled) => {
  if (missingCount === 0) {
    const clean = "No missing keywords detected. We removed any previous hidden keyword block for a clean export.";
    return aiEnabled ? `${clean} AI assist ran for cross-checking.` : clean;
  }
  const summary = `Injected ${missingCount} hidden keyword${missingCount === 1 ? "" : "s"} from ${candidateCount} high-value signals in the job post.`;
  return aiEnabled ? `${summary} AI assist provided additional keyword candidates.` : summary;
};

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetResults();
  setLoading(true);

  const formData = new FormData(form);

  try {
    const response = await fetch("/api/process", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({ error: "Unable to process request." }));
      renderWarnings([errorPayload.error || "Unknown error."]);
      setLoading(false);
      return;
    }

    const data = await response.json();
    latestResumeContent = data.updated_resume || "";
    currentCompanyName = data.company_name || "";

    renderStatus(
      buildSummary(data.missing_keywords.length, data.keyword_candidates.length, data.ai_enabled), 
      data.scraped_from_url,
      data.output_dir
    );
    renderWarnings(data.warnings || []);
    renderExtractedKeywords(data.keyword_candidates || [], data.missing_keywords || [], data.ai_keywords || [], data.ai_enabled);
    renderKeywords(data.missing_keywords || [], data.keyword_candidates || []);
    renderWhiteBlock(data.white_block || "");

    if (latestResumeContent) {
      downloadWrapper.classList.remove("hidden");
    }
  } catch (error) {
    renderWarnings(["Network error. Try again or paste the job description manually."]);
  } finally {
    setLoading(false);
  }
});

downloadButton.addEventListener("click", () => {
  if (!latestResumeContent) {
    return;
  }
  const blob = new Blob([latestResumeContent], { type: "text/x-tex" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "resume_updated.tex";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
});

const setPdfLoading = (isLoading) => {
  if (isLoading) {
    pdfButtonText.textContent = "Compiling PDF...";
    pdfButtonLoader.classList.remove("hidden");
    downloadPdfButton.setAttribute("disabled", "true");
  } else {
    pdfButtonText.textContent = "Download PDF (Chandan_Prakash_Software.pdf)";
    pdfButtonLoader.classList.add("hidden");
    downloadPdfButton.removeAttribute("disabled");
  }
};

downloadPdfButton.addEventListener("click", async () => {
  if (!latestResumeContent) {
    return;
  }

  setPdfLoading(true);

  try {
    const response = await fetch("/api/compile-pdf", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 
        latex_content: latestResumeContent,
        company_name: currentCompanyName
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "PDF compilation failed" }));
      alert(errorData.error || "PDF compilation failed. Please check your LaTeX syntax.");
      setPdfLoading(false);
      return;
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "Chandan_Prakash_Software.pdf";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (error) {
    alert("Network error during PDF compilation. Please try again.");
  } finally {
    setPdfLoading(false);
  }
});
