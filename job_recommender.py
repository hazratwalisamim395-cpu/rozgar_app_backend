import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class RecommendationEngine:

    def __init__(self, csv_file="acbar_jobs.csv"):

        # ==================================================
        # LOAD JOB DATA
        # ==================================================

        self.csv_file = csv_file

        self.df = pd.read_csv(csv_file)

        print(
            f"Loaded {len(self.df)} jobs"
        )


        # ==================================================
        # COLUMNS USED BY ML
        # ==================================================

        self.ml_columns = [
            "Title",
            "Category",
            "Education",
            "Experience",
            "Job Summary",
            "Job Requirements",
        ]


        # ==================================================
        # CREATE ML DATAFRAME
        # ==================================================

        self.ml_df = self.df[
            self.ml_columns
        ].copy()


        # ==================================================
        # HANDLE MISSING VALUES
        # ==================================================

        for column in self.ml_columns:

            self.ml_df[column] = (
                self.ml_df[column]
                .fillna("")
                .astype(str)
            )


        # ==================================================
        # CLEAN TEXT
        # ==================================================

        for column in self.ml_columns:

            self.ml_df[column] = (
                self.ml_df[column]
                .str.replace(
                    r"\s+",
                    " ",
                    regex=True
                )
                .str.strip()
            )


        # ==================================================
        # CREATE JOB TEXT
        # ==================================================

        self.ml_df["job_text"] = (

            self.ml_df["Title"] + " " +

            self.ml_df["Category"] + " " +

            self.ml_df["Education"] + " " +

            self.ml_df["Experience"] + " " +

            self.ml_df["Job Summary"] + " " +

            self.ml_df["Job Requirements"]
        )


        # ==================================================
        # CREATE TF-IDF VECTORIZER
        # ==================================================

        self.vectorizer = TfidfVectorizer(
            stop_words="english"
        )


        # ==================================================
        # FIT MODEL
        # ==================================================

        self.tfidf_matrix = (
            self.vectorizer.fit_transform(
                self.ml_df["job_text"]
            )
        )


        print(
            "TF-IDF matrix:",
            self.tfidf_matrix.shape
        )


    # ======================================================
    # RECOMMEND JOBS
    # ======================================================

    def recommend(
        self,
        user_profile,
        top_n=10
    ):

        # --------------------------------------------------
        # Validate profile
        # --------------------------------------------------

        if not user_profile:

            return []


        # --------------------------------------------------
        # Convert user profile → TF-IDF vector
        # --------------------------------------------------

        user_vector = (
            self.vectorizer.transform(
                [user_profile]
            )
        )


        # --------------------------------------------------
        # Calculate similarity
        # --------------------------------------------------

        similarity_scores = (
            cosine_similarity(
                user_vector,
                self.tfidf_matrix
            )[0]
        )


        # --------------------------------------------------
        # Sort jobs
        # --------------------------------------------------

        recommended_indices = (
            similarity_scores
            .argsort()[::-1]
        )


        # --------------------------------------------------
        # Limit results
        # --------------------------------------------------

        top_indices = (
            recommended_indices[:top_n]
        )


        # --------------------------------------------------
        # Create results
        # --------------------------------------------------

        results = []


        for index in top_indices:

            # Get original job row
            job = self.df.iloc[index]


            # Convert NaN values to None
            job_data = job.where(
                pd.notna(job),
                None
            ).to_dict()


            # Add ML score
            job_data["similarity"] = round(
                float(
                    similarity_scores[index]
                ),
                4
            )


            results.append(
                job_data
            )


        return results
