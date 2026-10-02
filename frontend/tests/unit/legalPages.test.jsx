// GIGW policy pages: every document exists in every language with the same sections, and renders with one h1.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LegalPage from "../../src/pages/legal/LegalPage";
import { legalContent } from "../../src/pages/legal/legalContent";

const DOCS = ["privacy", "terms", "accessibility"];

describe("policy pages", () => {
  it("each document has the same number of sections and items in en, hi and mr", () => {
    for (const doc of DOCS) {
      const shape = (lang) => legalContent[lang][doc].sections.map(([, paragraphs]) => paragraphs.length);
      expect(shape("hi"), `hi ${doc}`).toEqual(shape("en"));
      expect(shape("mr"), `mr ${doc}`).toEqual(shape("en"));
      for (const lang of ["en", "hi", "mr"]) {
        for (const [heading, paragraphs] of legalContent[lang][doc].sections) {
          expect(heading.trim(), `${lang} ${doc}`).not.toBe("");
          for (const p of paragraphs) expect(p.trim(), `${lang} ${doc} ${heading}`).not.toBe("");
        }
      }
    }
  });

  it("the privacy policy covers the DPDP essentials", () => {
    const text = JSON.stringify(legalContent.en.privacy);
    for (const must of ["Data Fiduciary", "Consent", "Grievance Officer", "Data Protection Board", "erased", "Children"]) {
      expect(text, must).toContain(must);
    }
  });

  it.each(DOCS)("%s renders one main heading and its sections", (doc) => {
    render(<LegalPage doc={doc} />);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getAllByRole("heading", { level: 2 }).length).toBe(legalContent.en[doc].sections.length);
  });
});
