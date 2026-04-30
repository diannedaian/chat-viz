export const RELATIONSHIP_COPY = {
  romantic: {
    subtitle: "A love story in messages",
    endingTitle: "Forever",
    endingTagline: "and counting",
    icon: "♡",
  },
  friendship: {
    subtitle: "A friendship story in messages",
    endingTitle: "Life Long Friendship",
    endingTagline: "days strong",
    icon: "✦",
  },
  family: {
    subtitle: "A family story in messages",
    endingTitle: "Family Love",
    endingTagline: "days together",
    icon: "❀",
  },
};

export function getRelationshipCopy(type) {
  return RELATIONSHIP_COPY[type] || RELATIONSHIP_COPY.romantic;
}
