import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faLock, faLockOpen } from "@fortawesome/free-solid-svg-icons";

import { api } from "@mwdb-web/commons/api";
import {
    LimitTo,
    UserBadge,
    PagedList,
    HighlightText,
} from "@mwdb-web/commons/ui";
import { useViewAlert } from "@mwdb-web/commons/hooks";

function GroupItem(props) {
    const lockAttributes = props.immutable
        ? { icon: faLock, tip: "Immutable group" }
        : { icon: faLockOpen, tip: "Mutable group" };

    return (
        <tr key={props.name}>
            <td>
                <Link to={`/settings/group/${props.name}`}>
                    <HighlightText filterValue={props.filterValue}>
                        {props.name}
                    </HighlightText>
                </Link>
                <span data-toggle="tooltip" title={lockAttributes.tip}>
                    <FontAwesomeIcon
                        icon={lockAttributes.icon}
                        pull="left"
                        size="1x"
                        style={{ color: "grey" }}
                    />
                </span>
            </td>
            <td>
                {props.name === "public" ? (
                    "(Group is public and contains all members)"
                ) : (
                    <LimitTo count={5}>
                        {props.users.map((login) => (
                            <UserBadge
                                key={login}
                                user={{ login }}
                                clickable
                                basePath="/settings"
                            />
                        ))}
                    </LimitTo>
                )}
            </td>
        </tr>
    );
}

export default function GroupsList() {
    const { setAlert } = useViewAlert();
    const [groups, setGroups] = useState([]);
    const [activePage, setActivePage] = useState(1);
    const [groupFilter, setGroupFilter] = useState("");

    const query = groupFilter.toLowerCase();
    const items = groups
        .filter((group) => !group.private)
        .filter((group) => group.name.toLowerCase().includes(query))
        .sort((groupA, groupB) => groupA.name.localeCompare(groupB.name));

    useEffect(() => {
        getGroups();
    }, []);

    async function getGroups() {
        try {
            const response = await api.getGroups();
            setGroups(response.data["groups"]);
        } catch (error) {
            setAlert({ error });
        }
    }

    return (
        <div className="container">
            <Link to="/settings/group/new">
                <button type="button" className="btn btn-success">
                    Create group
                </button>
            </Link>
            <PagedList
                listItem={GroupItem}
                columnNames={["Name", "Members"]}
                items={items.slice((activePage - 1) * 10, activePage * 10)}
                itemCount={items.length}
                activePage={activePage}
                filterValue={groupFilter}
                onPageChange={(pageNumber) => setActivePage(pageNumber)}
                onFilterChange={(ev) => {
                    setGroupFilter(ev.target.value);
                    setActivePage(1);
                }}
            />
        </div>
    );
}
