// This file is part of InvenioRDM
// Copyright (C) 2023 CERN.
// Copyright (C) 2022-2024 KTH Royal Institute of Technology.
//
// Invenio App RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

/**
 * This overrides is been updated to v12.0.2
 * Overrides:
 * - RecommendedInformation: Added CommunityHeader on top of Recommended information section.
 * - CommunityHeader: Added a message to inform user that community is required in order to submit data.
 * - CommunityHeader: Added a check to hide community msg if community is already selected.
 * - Add custom locale message for community required.
 */

// https://github.com/inveniosoftware/invenio-app-rdm/blob/v12.0.2/invenio_app_rdm/theme/assets/semantic-ui/js/invenio_app_rdm/deposit/RDMDepositForm.js
// Note: Overriding the Uploads component results in issues showing new version btn on edit record page.
// this is why we moved the override to the RecommendedInformationOverride component where its more stable.

import _isEmpty from "lodash/isEmpty";
import PropTypes from "prop-types";
import { i18next } from "@translations/invenio_app_rdm/i18next";
import React from "react";
import { AccordionField, FieldLabel } from "react-invenio-forms";
import _get from "lodash/get";
import {
  CreatibutorsField,
  CommunityHeader,
  PublisherField,
  LanguagesField,
  SubjectsField,
  VersionField,
  DatesField,
} from "@js/invenio_rdm_records";
import { Container, Divider, Card, Grid, Form } from "semantic-ui-react";
import { getLocale, getCurrentLocaleMessage } from "../utils/index.js";

const REQ_COMM_MSG = {
  en: "Community is required in order to submit your record.",
  sv: "Community krävs för att skicka in din post.",
};

// Function to check if a community is selected
const isCommunitySelected = (record) => {
  const reviewCommunityId = record.parent?.review?.receiver?.community;
  const defaultCommunityId = record.parent?.communities?.default;
  const hasCommunity = reviewCommunityId || defaultCommunityId;

  // Community is not selected
  if (!hasCommunity) {
    return false;
  }

  const alreadyPublished = ["published", "new_version_draft"].includes(
    record.status
  );

  // Community is selected if record is expanded
  const selectedCommunity = alreadyPublished
    ? record.expanded?.parent?.communities?.default
    : record.expanded?.parent?.review?.receiver;

  return !_isEmpty(selectedCommunity);
};

export const RecommendedInformationOverride = ({
  vocabularies,
  config,
  record,
}) => {
  const locale = getLocale();
  const currentLocalReqCommMsg = getCurrentLocaleMessage(REQ_COMM_MSG, locale);
  const recHasCommunity = isCommunitySelected(record);
  const hideCommunitySelection = config.hide_community_selection || false;

  return (
    <>
      <AccordionField active label={i18next.t("Community")}>
        <Grid>
          <Grid.Row className="pb-0">
            <Grid.Column>
              {!recHasCommunity && (
                <>
                  <Form.Field required id="communityRequiredMessage">
                    <Card.Content>
                      <Card.Header>
                        <FieldLabel
                          className="ui grid visible info message header "
                          htmlFor="communityHeader"
                          label={currentLocalReqCommMsg}
                        />
                      </Card.Header>
                    </Card.Content>
                  </Form.Field>
                  <Divider horizontal />
                </>
              )}
              <Container className="ui grid page-subheader pb-5">
                {!hideCommunitySelection && (
                  <CommunityHeader
                    imagePlaceholderLink="/static/images/square-placeholder.png"
                    record={record}
                  />
                )}
              </Container>
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </AccordionField>
      <AccordionField
        includesPaths={[
          "metadata.contributors",
          "metadata.subjects",
          "metadata.languages",
          "metadata.dates",
          "metadata.version",
          "metadata.publisher",
        ]}
        active
        label={i18next.t("Recommended information")}
      >
        <CreatibutorsField
          addButtonLabel={i18next.t("Add contributor")}
          label={i18next.t("Contributors")}
          labelIcon="user plus"
          fieldPath="metadata.contributors"
          roleOptions={vocabularies.metadata.contributors.role}
          schema="contributors"
          autocompleteNames={config.autocomplete_names}
          modal={{
            addLabel: "Add contributor",
            editLabel: "Edit contributor",
          }}
        />
        <SubjectsField
          fieldPath="metadata.subjects"
          initialOptions={_get(record, "ui.subjects", null)}
          limitToOptions={vocabularies.metadata.subjects.limit_to}
        />

        <LanguagesField
          fieldPath="metadata.languages"
          initialOptions={_get(record, "ui.languages", []).filter(
            (lang) => lang !== null
          )} // needed because dumped empty record from backend gives [null]
          serializeSuggestions={(suggestions) =>
            suggestions.map((item) => ({
              text: item.title_l10n,
              value: item.id,
              key: item.id,
            }))
          }
        />

        <DatesField
          fieldPath="metadata.dates"
          options={vocabularies.metadata.dates}
          showEmptyValue
        />
        <VersionField fieldPath="metadata.version" />
        <PublisherField fieldPath="metadata.publisher" />
      </AccordionField>
    </>
  );
};

RecommendedInformationOverride.propTypes = {
  config: PropTypes.object,
  record: PropTypes.object,
  vocabularies: PropTypes.object,
};

RecommendedInformationOverride.defaultProps = {
  config: {},
  record: {},
  vocabularies: {},
};
